from datetime import date, timedelta

from django.db.models import Q, Sum, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Account
from accounts.serializer import AccountSerializer
from common import serializer, swagger_params
from common.models import Activity, Profile
from common.utils import STAGES
from contacts.models import Contact
from contacts.serializer import ContactSerializer
from leads.models import Lead
from leads.serializer import LeadSerializer
from opportunity.models import Opportunity
from opportunity.serializer import OpportunitySerializer
from tasks.models import Task
from tasks.serializer import TaskSerializer


class ApiHomeView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["home"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="ApiHomeResponse",
                fields={
                    "accounts_count": serializers.IntegerField(),
                    "contacts_count": serializers.IntegerField(),
                    "leads_count": serializers.IntegerField(),
                    "opportunities_count": serializers.IntegerField(),
                    "accounts": AccountSerializer(many=True),
                    "contacts": ContactSerializer(many=True),
                    "leads": LeadSerializer(many=True),
                    "opportunities": OpportunitySerializer(many=True),
                },
            )
        },
    )
    def get(self, request, format=None):
        if not request.profile:
            return Response({"error": "Profile not found"}, status=status.HTTP_403_FORBIDDEN)
        org = request.profile.org
        profile = request.profile
        today = date.today()

        is_admin = profile.role == "ADMIN" or request.user.is_superuser

        accounts = Account.objects.filter(is_active=True, org=org)
        contacts = Contact.objects.filter(org=org)
        leads = Lead.objects.filter(org=org).exclude(
            Q(status="converted") | Q(status="closed")
        )
        opportunities = Opportunity.objects.filter(org=org)
        tasks = Task.objects.filter(org=org)

        if not is_admin:
            accounts = accounts.filter(Q(created_by=request.user) | Q(assigned_to=profile)).distinct()
            contacts = contacts.filter(Q(created_by=request.user) | Q(assigned_to=profile)).distinct()
            leads = leads.filter(Q(created_by=request.user) | Q(assigned_to=profile)).distinct()
            opportunities = opportunities.filter(Q(created_by=request.user) | Q(assigned_to=profile)).distinct()
            tasks = tasks.filter(Q(created_by=request.user) | Q(assigned_to=profile)).distinct()

        # Build base context (existing)
        context = {}
        context["accounts_count"] = accounts.count()
        context["contacts_count"] = contacts.count()
        context["leads_count"] = leads.count()
        context["opportunities_count"] = opportunities.count()
        context["accounts"] = AccountSerializer(accounts, many=True).data
        context["contacts"] = ContactSerializer(contacts, many=True).data
        context["leads"] = LeadSerializer(leads, many=True).data
        context["opportunities"] = OpportunitySerializer(opportunities, many=True).data

        # NEW: Urgent counts for Focus Bar
        overdue_tasks = tasks.filter(
            status__in=["New", "In Progress"], due_date__lt=today
        ).count()

        tasks_due_today = tasks.filter(
            status__in=["New", "In Progress"], due_date=today
        ).count()

        followups_today = leads.filter(next_follow_up=today).count()

        hot_leads = leads.filter(
            rating="HOT", status__in=["assigned", "in process"]
        ).count()

        context["urgent_counts"] = {
            "overdue_tasks": overdue_tasks,
            "tasks_due_today": tasks_due_today,
            "followups_today": followups_today,
            "hot_leads": hot_leads,
        }

        # Get org's default currency for filtering
        org_currency = org.default_currency or "USD"

        # NEW: Pipeline by stage (filtered by org's default currency)
        # Only sum amounts that match org's currency for accurate totals
        pipeline_by_stage = {}
        for stage_code, stage_label in STAGES:
            stage_opps = opportunities.filter(stage=stage_code)
            # Filter by currency for value calculation (include null as matching org currency)
            stage_opps_with_currency = stage_opps.filter(
                Q(currency=org_currency) | Q(currency__isnull=True) | Q(currency="")
            )
            stage_value = stage_opps_with_currency.aggregate(
                total=Coalesce(Sum("amount"), 0, output_field=DecimalField())
            )["total"]
            pipeline_by_stage[stage_code] = {
                "count": stage_opps.count(),  # Count all opportunities
                "value": float(stage_value or 0),  # Value only for matching currency
                "label": stage_label,
            }
        context["pipeline_by_stage"] = pipeline_by_stage

        # NEW: Revenue metrics (filtered by org's default currency)
        open_stages = ["PROSPECTING", "QUALIFICATION", "PROPOSAL", "NEGOTIATION"]
        open_opps = opportunities.filter(stage__in=open_stages)
        # Filter by currency for value calculations
        open_opps_with_currency = open_opps.filter(
            Q(currency=org_currency) | Q(currency__isnull=True) | Q(currency="")
        )

        pipeline_value = open_opps_with_currency.aggregate(
            total=Coalesce(Sum("amount"), 0, output_field=DecimalField())
        )["total"]

        # Weighted pipeline = sum of (amount * probability / 100)
        weighted_pipeline = open_opps_with_currency.aggregate(
            total=Coalesce(
                Sum(F("amount") * F("probability") / 100),
                0,
                output_field=DecimalField(),
            )
        )["total"]

        # Won this month (use timezone-aware datetime for updated_at comparison)
        now = timezone.now()
        first_day_of_month = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        won_opps = opportunities.filter(
            stage="CLOSED_WON", updated_at__gte=first_day_of_month
        )
        won_opps_with_currency = won_opps.filter(
            Q(currency=org_currency) | Q(currency__isnull=True) | Q(currency="")
        )
        won_this_month = won_opps_with_currency.aggregate(
            total=Coalesce(Sum("amount"), 0, output_field=DecimalField())
        )["total"]

        # Conversion rate: leads converted / total leads
        total_leads_all = Lead.objects.filter(org=org).count()
        converted_leads = Lead.objects.filter(org=org, status="converted").count()
        conversion_rate = (
            (converted_leads / total_leads_all * 100) if total_leads_all > 0 else 0
        )

        # Count opportunities in other currencies (for info)
        other_currency_count = opportunities.exclude(
            Q(currency=org_currency) | Q(currency__isnull=True) | Q(currency="")
        ).count()

        context["revenue_metrics"] = {
            "pipeline_value": float(pipeline_value or 0),
            "weighted_pipeline": float(weighted_pipeline or 0),
            "won_this_month": float(won_this_month or 0),
            "conversion_rate": round(conversion_rate, 1),
            "currency": org_currency,
            "other_currency_count": other_currency_count,
        }

        # NEW: Hot leads list for dedicated panel
        hot_leads_qs = leads.filter(
            rating="HOT", status__in=["assigned", "in process"]
        ).order_by("-created_at")[:10]

        context["hot_leads"] = [
            {
                "id": str(lead.id),
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company": lead.company_name,
                "rating": lead.rating,
                "next_follow_up": lead.next_follow_up.isoformat()
                if lead.next_follow_up
                else None,
                "last_contacted": lead.last_contacted.isoformat()
                if lead.last_contacted
                else None,
            }
            for lead in hot_leads_qs
        ]

        # Include tasks in dashboard response (avoid separate API call)
        upcoming_tasks = tasks.filter(
            status__in=["New", "In Progress"], due_date__isnull=False
        ).order_by("due_date")[:10]
        context["tasks"] = TaskSerializer(upcoming_tasks, many=True).data

        # Goal summary for current user
        from opportunity.models import SalesGoal

        goal_filter = Q(assigned_to=profile) | Q(team__in=profile.user_teams.all())
        if is_admin:
            goal_filter |= Q(assigned_to__isnull=True, team__isnull=True)

        active_goals = (
            SalesGoal.objects.filter(
                org=org,
                is_active=True,
                period_start__lte=today,
                period_end__gte=today,
            )
            .filter(goal_filter)
            .distinct()[:3]
        )
        context["goal_summary"] = [
            {
                "id": str(g.id),
                "name": g.name,
                "goal_type": g.goal_type,
                "target_value": float(g.target_value),
                "progress_value": float(g.compute_progress()),
                "progress_percent": g.progress_percent,
                "status": g.status,
            }
            for g in active_goals
        ]

        # Team/Personal performance metrics
        week_start = today - timedelta(days=today.weekday())  # Monday
        month_start = today.replace(day=1)

        def compute_user_stats(user):
            """Compute performance stats for a given User."""
            user_profile = Profile.objects.filter(org=org, user=user).first()
            if user_profile:
                user_leads = Lead.objects.filter(org=org).filter(
                    Q(created_by=user) | Q(assigned_to=user_profile)
                ).distinct()
                user_contacts = Contact.objects.filter(org=org).filter(
                    Q(created_by=user) | Q(assigned_to=user_profile)
                ).distinct()
                user_accounts = Account.objects.filter(org=org, is_active=True).filter(
                    Q(created_by=user) | Q(assigned_to=user_profile)
                ).distinct()
            else:
                user_leads = Lead.objects.filter(org=org, created_by=user)
                user_contacts = Contact.objects.filter(org=org, created_by=user)
                user_accounts = Account.objects.filter(org=org, created_by=user, is_active=True)
            user_followups = user_leads.filter(next_follow_up__isnull=False)

            return {
                "leads_count": user_leads.count(),
                "leads_today": user_leads.filter(created_at__date=today).count(),
                "leads_week": user_leads.filter(created_at__date__gte=week_start).count(),
                "leads_month": user_leads.filter(created_at__date__gte=month_start).count(),
                "contacts_count": user_contacts.count(),
                "accounts_count": user_accounts.count(),
                "followups_today": user_followups.filter(next_follow_up=today).count(),
                "followups_week": user_followups.filter(
                    next_follow_up__gte=week_start, next_follow_up__lte=today
                ).count(),
                "followups_month": user_followups.filter(
                    next_follow_up__gte=month_start, next_follow_up__lte=today
                ).count(),
                "followups_total": user_followups.count(),
            }

        my_stats = compute_user_stats(request.user)

        team_members = []
        if is_admin:
            profiles_qs = Profile.objects.filter(
                org=org, is_active=True
            ).select_related("user")
            for p in profiles_qs:
                user_stats = compute_user_stats(p.user)
                team_members.append({
                    "user_id": str(p.user.id),
                    "user_name": p.user.name or p.user.email or p.user.phone or "",
                    "user_email": p.user.email or "",
                    "role": p.role,
                    "stats": user_stats,
                })

        context["is_admin"] = is_admin
        context["team_performance"] = {
            "my_stats": my_stats,
            "team_members": team_members,
        }

        # Include recent activities (avoid separate API call)
        activities = (
            Activity.objects.filter(org=org)
            .select_related("user", "user__user")
            .order_by("-created_at")[:10]
        )
        context["activities"] = serializer.ActivitySerializer(
            activities, many=True
        ).data

        return Response(context, status=status.HTTP_200_OK)


class ActivityListView(APIView):
    """
    Get recent activities for the organization with advanced filtering.
    Returns the last 10 activities by default.
    Supports pagination, filtering by user, action, entity_type, and date range.
    """

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["activities"],
        parameters=swagger_params.organization_params
        + [
            OpenApiParameter(
                name="limit",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Number of activities to return (default: 10, max: 100)",
            ),
            OpenApiParameter(
                name="offset",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Offset for pagination",
            ),
            OpenApiParameter(
                name="entity_type",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by entity type (Account, Lead, Contact, etc.)",
            ),
            OpenApiParameter(
                name="action",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by action (CREATE, UPDATE, DELETE, etc.)",
            ),
            OpenApiParameter(
                name="user_id",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by user/profile UUID",
            ),
            OpenApiParameter(
                name="date_from",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Start date (YYYY-MM-DD)",
            ),
            OpenApiParameter(
                name="date_to",
                type=str,
                location=OpenApiParameter.QUERY,
                description="End date (YYYY-MM-DD)",
            ),
        ],
        responses={200: serializer.ActivitySerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        if not request.profile:
            return Response(
                {"error": True, "errors": "Organization context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Only admin/superuser can see all activities
        is_admin = request.profile.role == "ADMIN" or request.user.is_superuser

        # Get query params
        limit = min(int(request.query_params.get("limit", 20)), 100)
        offset = int(request.query_params.get("offset", 0))
        entity_type = request.query_params.get("entity_type", None)
        action = request.query_params.get("action", None)
        user_id = request.query_params.get("user_id", None)
        date_from = request.query_params.get("date_from", None)
        date_to = request.query_params.get("date_to", None)

        # Query activities for this organization — all members see all activities
        queryset = Activity.objects.filter(org=request.profile.org)

        # Filter by entity type if specified
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)

        # Filter by action if specified
        if action:
            actions = [a.strip() for a in action.split(",")]
            queryset = queryset.filter(action__in=actions)

        # Filter by user if specified (admin only)
        if user_id and is_admin:
            queryset = queryset.filter(user__id=user_id)

        # Filter by date range
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        # Get total count before pagination
        total_count = queryset.count()

        # Get most recent activities with pagination
        activities = (
            queryset.select_related("user", "user__user")
            .order_by("-created_at")[offset:offset + limit]
        )

        # Serialize
        activities_data = serializer.ActivitySerializer(activities, many=True).data

        return Response(
            {
                "error": False,
                "total_count": total_count,
                "count": len(activities_data),
                "offset": offset,
                "limit": limit,
                "activities": activities_data,
            },
            status=status.HTTP_200_OK,
        )
