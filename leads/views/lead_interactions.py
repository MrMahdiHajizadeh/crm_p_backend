from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.models import APISettings, Attachments, Comment
from common.permissions import HasOrgContext
from common.serializer import AttachmentsSerializer, CommentSerializer, LeadCommentSerializer
from contacts.models import Contact
from leads import swagger_params
from leads.forms import LeadListForm
from leads.models import InteractionLog, Lead
from leads.serializer import (
    CreateLeadFromSiteSwaggerSerializer,
    InteractionLogCreateSerializer,
    InteractionLogSerializer,
    LeadCommentEditSwaggerSerializer,
    LeadUploadSwaggerSerializer,
)
from leads.tasks import create_lead_from_file, send_lead_assigned_emails


class LeadUploadView(APIView):
    model = Lead
    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        request=LeadUploadSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="LeadUploadResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def post(self, request, *args, **kwargs):
        lead_form = LeadListForm(request.POST, request.FILES)
        if lead_form.is_valid():
            create_lead_from_file.delay(
                lead_form.validated_rows,
                lead_form.invalid_rows,
                request.profile.id,
                request.get_host(),
                request.profile.org.id,
            )
            return Response(
                {"error": False, "message": "Leads created Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": lead_form.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LeadCommentView(APIView):
    model = Comment
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk, org=self.request.profile.org)

    def get_lead(self, pk):
        from leads.models import Lead
        return Lead.objects.get(pk=pk, org=self.request.profile.org)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        responses={200: CommentSerializer(many=True)},
        description="List comments for a lead, or get a single comment by ID",
    )
    def get(self, request, pk, format=None):
        """Get comments for a lead, or a single comment by its ID."""
        # Try to get by comment ID first
        try:
            comment = self.get_object(pk)
            return Response(CommentSerializer(comment).data)
        except self.model.DoesNotExist:
            pass

        # If not found as comment, treat pk as lead ID and return all comments
        from django.contrib.contenttypes.models import ContentType
        lead = self.get_lead(pk)
        content_type = ContentType.objects.get_for_model(lead.__class__)
        comments = self.model.objects.filter(
            content_type=content_type,
            object_id=lead.id,
            org=request.profile.org,
        ).order_by("-id")
        return Response(CommentSerializer(comments, many=True).data)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        request=LeadCommentEditSwaggerSerializer,
        responses={
            201: CommentSerializer(),
        },
    )
    def post(self, request, pk, format=None):
        """Create a new comment on a lead."""
        from django.contrib.contenttypes.models import ContentType

        lead = self.get_lead(pk)
        text = request.data.get("comment", "").strip()
        if not text:
            return Response(
                {"error": True, "errors": {"comment": "Comment text is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        content_type = ContentType.objects.get_for_model(lead.__class__)
        comment = Comment.objects.create(
            content_type=content_type,
            object_id=lead.id,
            comment=text,
            commented_by=request.profile,
            org=request.profile.org,
        )
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        request=LeadCommentEditSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="LeadCommentUpdateResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def put(self, request, pk, format=None):
        params = request.data
        obj = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
            or request.profile == obj.commented_by
        ):
            serializer = LeadCommentSerializer(obj, data=params)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"error": False, "message": "Comment Submitted"},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "error": True,
                "errors": "You don't have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        request=LeadCommentEditSwaggerSerializer,
        description="Partial Comment Update",
        responses={
            200: inline_serializer(
                name="LeadCommentPatchResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def patch(self, request, pk, format=None):
        """Handle partial updates to a comment."""
        params = request.data
        obj = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
            or request.profile == obj.commented_by
        ):
            serializer = LeadCommentSerializer(obj, data=params, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"error": False, "message": "Comment Updated"},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "error": True,
                "errors": "You don't have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="LeadCommentDeleteResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
            or request.profile == self.object.commented_by
        ):
            self.object.delete()
            return Response(
                {"error": False, "message": "Comment Deleted Successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "error": True,
                "errors": "You do not have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class LeadAttachmentView(APIView):
    model = Attachments
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    def get_lead(self, pk):
        return Lead.objects.get(pk=pk, org=self.request.profile.org)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        responses={200: AttachmentsSerializer(many=True)},
        description="List attachments for a lead, or get a single attachment by ID",
    )
    def get(self, request, pk, format=None):
        """Get attachments for a lead, or a single attachment by its ID."""
        try:
            attachment = self.get_object(pk)
            return Response(AttachmentsSerializer(attachment).data)
        except self.model.DoesNotExist:
            pass

        lead = self.get_lead(pk)
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(lead.__class__)
        attachments = self.model.objects.filter(
            content_type=content_type,
            object_id=lead.id,
            org=request.profile.org,
        ).order_by("-id")
        return Response(AttachmentsSerializer(attachments, many=True).data)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="LeadAttachmentDeleteResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def delete(self, request, pk, format=None):
        self.object = self.model.objects.get(pk=pk)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
            or request.profile.user == self.object.created_by
        ):
            self.object.delete()
            return Response(
                {"error": False, "message": "Attachment Deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "error": True,
                "errors": "You don't have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class LeadInteractionListCreateView(APIView):
    """
    GET /api/leads/interactions/ — list all interactions for the org (with filters)
    POST /api/leads/interactions/ — create a new interaction
    """

    model = InteractionLog
    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        responses={200: InteractionLogSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        queryset = InteractionLog.objects.filter(org=request.profile.org)

        # Filter by entity
        entity_type = request.query_params.get("entity_type")
        entity_id = request.query_params.get("entity_id")
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)

        # Filter by follow-up status
        follow_up = request.query_params.get("follow_up")
        if follow_up == "pending":
            queryset = queryset.filter(
                follow_up_date__isnull=False,
                follow_up_date__gte=timezone.now()
            )
        elif follow_up == "overdue":
            queryset = queryset.filter(
                follow_up_date__isnull=False,
                follow_up_date__lt=timezone.now()
            )
        elif follow_up == "all":
            queryset = queryset.filter(follow_up_date__isnull=False)

        # Filter by interaction type
        interaction_type = request.query_params.get("interaction_type")
        if interaction_type:
            queryset = queryset.filter(interaction_type=interaction_type)

        # Date range
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(interaction_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(interaction_date__lte=date_to)

        queryset = queryset.order_by("-interaction_date")
        return Response(InteractionLogSerializer(queryset, many=True).data)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        request=InteractionLogCreateSerializer,
        responses={201: InteractionLogSerializer()},
    )
    def post(self, request, *args, **kwargs):
        serializer = InteractionLogCreateSerializer(data=request.data)
        if serializer.is_valid():
            interaction = serializer.save(
                org=request.profile.org,
                created_by=request.user,
            )
            # If this interaction has a follow_up_date, also update the lead's next_follow_up
            if (
                interaction.entity_type == "Lead"
                and interaction.follow_up_date
            ):
                try:
                    lead = Lead.objects.get(id=interaction.entity_id, org=request.profile.org)
                    lead.next_follow_up = interaction.follow_up_date.date()
                    lead.last_contacted = interaction.interaction_date.date()
                    lead.save(update_fields=["next_follow_up", "last_contacted"])
                except Lead.DoesNotExist:
                    pass
            return Response(
                InteractionLogSerializer(interaction).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LeadScopedInteractionView(APIView):
    """
    GET /api/leads/<pk>/interactions/ — list interactions for a specific lead
    POST /api/leads/<pk>/interactions/ — create interaction for a specific lead
    """

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_lead(self, pk):
        from leads.models import Lead
        return get_object_or_404(Lead, id=pk, org=self.request.profile.org)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        responses={200: InteractionLogSerializer(many=True)},
    )
    def get(self, request, pk, *args, **kwargs):
        lead = self.get_lead(pk)
        interactions = InteractionLog.objects.filter(
            org=request.profile.org,
            entity_type="Lead",
            entity_id=lead.id,
        ).order_by("-interaction_date")
        return Response(InteractionLogSerializer(interactions, many=True).data)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        request=InteractionLogCreateSerializer,
        responses={201: InteractionLogSerializer()},
    )
    def post(self, request, pk, *args, **kwargs):
        lead = self.get_lead(pk)
        serializer = InteractionLogCreateSerializer(data=request.data)
        if serializer.is_valid():
            interaction = serializer.save(
                org=request.profile.org,
                entity_type="Lead",
                entity_id=lead.id,
                created_by=request.user,
            )
            # Update lead's last_contacted and next_follow_up
            lead.last_contacted = interaction.interaction_date.date()
            if interaction.follow_up_date:
                lead.next_follow_up = interaction.follow_up_date.date()
            lead.save(update_fields=["last_contacted", "next_follow_up"])
            return Response(
                InteractionLogSerializer(interaction).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class InteractionLogDetailView(APIView):
    """
    GET/PUT/PATCH/DELETE /api/leads/interactions/<pk>/
    """

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return get_object_or_404(InteractionLog, pk=pk, org=self.request.profile.org)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        responses={200: InteractionLogSerializer()},
    )
    def get(self, request, pk, *args, **kwargs):
        interaction = self.get_object(pk)
        return Response(InteractionLogSerializer(interaction).data)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        request=InteractionLogCreateSerializer,
        responses={200: InteractionLogSerializer()},
    )
    def put(self, request, pk, *args, **kwargs):
        interaction = self.get_object(pk)
        serializer = InteractionLogCreateSerializer(interaction, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(InteractionLogSerializer(interaction).data)
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        request=InteractionLogCreateSerializer,
        responses={200: InteractionLogSerializer()},
    )
    def patch(self, request, pk, *args, **kwargs):
        interaction = self.get_object(pk)
        serializer = InteractionLogCreateSerializer(
            interaction, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(InteractionLogSerializer(interaction).data)
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        responses={204: None},
    )
    def delete(self, request, pk, *args, **kwargs):
        interaction = self.get_object(pk)
        interaction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowUpListView(APIView):
    """
    GET /api/leads/follow-ups/ — list all items needing follow-up
    Returns unified list of interactions with pending follow_up_date,
    grouped by recency (overdue, today, tomorrow, this week, later).
    """

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        responses={200: InteractionLogSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timezone.timedelta(days=1)
        tomorrow_end = today_end + timezone.timedelta(days=1)
        week_end = today_start + timezone.timedelta(days=7)

        my_only = request.query_params.get("my_only", "").lower() == "true"

        base_qs = InteractionLog.objects.filter(
            org=request.profile.org,
            follow_up_date__isnull=False,
        ).select_related("created_by")

        if my_only:
            base_qs = base_qs.filter(created_by=request.user)

        result = {
            "overdue": [],
            "today": [],
            "tomorrow": [],
            "this_week": [],
            "later": [],
        }

        for interaction in base_qs.order_by("follow_up_date"):
            fud = interaction.follow_up_date
            data = InteractionLogSerializer(interaction).data

            if fud < today_start:
                result["overdue"].append(data)
            elif fud < today_end:
                result["today"].append(data)
            elif fud < tomorrow_end:
                result["tomorrow"].append(data)
            elif fud < week_end:
                result["this_week"].append(data)
            else:
                result["later"].append(data)

        return Response(result)


class CreateLeadFromSite(APIView):
    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        request=CreateLeadFromSiteSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="CreateLeadFromSiteResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def post(self, request, *args, **kwargs):
        params = request.data
        api_key = params.get("apikey")
        # api_setting = APISettings.objects.filter(
        #     website=website_address, apikey=api_key).first()
        api_setting = APISettings.objects.filter(apikey=api_key).first()
        if not api_setting:
            return Response(
                {
                    "error": True,
                    "message": "You don't have permission, please contact the admin!.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if api_setting and params.get("email"):
            # user = User.objects.filter(is_admin=True, is_active=True).first()
            user = api_setting.created_by
            lead = Lead.objects.create(
                salutation=params.get(
                    "title"
                ),  # 'title' param maps to salutation for backwards compatibility
                first_name=params.get("first_name"),
                last_name=params.get("last_name"),
                status="assigned",
                source=api_setting.website,
                description=params.get("message"),
                email=params.get("email"),
                phone=params.get("phone"),
                is_active=True,
                created_by=user,
                org=api_setting.org,
            )
            lead.assigned_to.add(user)
            # Send Email to Assigned Users
            site_address = request.scheme + "://" + request.META["HTTP_HOST"]
            send_lead_assigned_emails.delay(
                lead.id, [user.id], site_address, str(api_setting.org.id)
            )
            # Create Contact
            try:
                contact = Contact.objects.create(
                    first_name=params.get("first_name") or "",
                    last_name=params.get("last_name") or "",
                    email=params.get("email"),
                    phone=params.get("phone"),
                    description=params.get("message"),
                    created_by=user,
                    is_active=True,
                    org=api_setting.org,
                )
                contact.assigned_to.add(user)

                lead.contacts.add(contact)
            except Exception:
                pass

            return Response(
                {"error": False, "message": "Lead Created sucessfully."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "message": "Invalid data"},
            status=status.HTTP_400_BAD_REQUEST,
        )
