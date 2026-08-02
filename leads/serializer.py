from rest_framework import serializers

from common.serializer import (
    AttachmentsSerializer,
    LeadCommentSerializer,
    ProfileSerializer,
    TagsSerializer,
    TeamsSerializer,
    UserSerializer,
)
from common.utils import LEAD_STATUS
from contacts.serializer import ContactSerializer
from leads.models import (
    INTERACTION_RESULT_CHOICES,
    INTERACTION_TYPE_CHOICES,
    InteractionLog,
    Lead,
    LeadPipeline,
    LeadStage,
)


class InteractionLogSerializer(serializers.ModelSerializer):
    """Serializer for interaction logs (read)."""

    created_by = UserSerializer(read_only=True)
    interaction_type_display = serializers.SerializerMethodField()
    result_display = serializers.SerializerMethodField()
    entity_name = serializers.SerializerMethodField()

    class Meta:
        model = InteractionLog
        fields = (
            "id",
            "entity_type",
            "entity_id",
            "entity_name",
            "interaction_type",
            "interaction_type_display",
            "interaction_date",
            "duration_minutes",
            "subject",
            "description",
            "result",
            "result_display",
            "follow_up_date",
            "created_by",
            "created_at",
            "updated_at",
        )

    def get_interaction_type_display(self, obj):
        return obj.get_interaction_type_display()

    def get_result_display(self, obj):
        return obj.get_result_display() if obj.result else None

    def get_entity_name(self, obj):
        """Resolve the display name of the linked entity."""
        from accounts.models import Account
        from contacts.models import Contact
        from leads.models import Lead
        from opportunity.models import Opportunity
        try:
            if obj.entity_type == "Lead":
                lead = Lead.objects.get(id=obj.entity_id)
                return lead.title or lead.email or str(lead) or f"Lead {lead.id}"
            elif obj.entity_type == "Contact":
                contact = Contact.objects.get(id=obj.entity_id)
                return str(contact) or contact.email or f"Contact {contact.id}"
            elif obj.entity_type == "Account":
                account = Account.objects.get(id=obj.entity_id)
                return account.name or f"Account {account.id}"
            elif obj.entity_type == "Opportunity":
                opp = Opportunity.objects.get(id=obj.entity_id)
                return opp.name or f"Opportunity {opp.id}"
        except Exception:
            pass
        return f"[Deleted {obj.entity_type}]"


class InteractionLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating interaction logs."""

    class Meta:
        model = InteractionLog
        fields = (
            "entity_type",
            "entity_id",
            "interaction_type",
            "interaction_date",
            "duration_minutes",
            "subject",
            "description",
            "result",
            "follow_up_date",
        )

    def validate_entity_type(self, value):
        valid_types = dict(InteractionLog.ENTITY_TYPE_CHOICES)
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid entity type. Must be one of: {', '.join(valid_types.keys())}")
        return value


class LeadSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    created_by = UserSerializer()
    tags = TagsSerializer(read_only=True, many=True)
    lead_attachment = AttachmentsSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    lead_comments = LeadCommentSerializer(read_only=True, many=True)

    class Meta:
        model = Lead
        fields = (
            "id",
            # Core Lead Information
            "title",
            "salutation",
            "first_name",
            "last_name",
            "email",
            "phone",
            "job_title",
            "website",
            "linkedin_url",
            # Sales Pipeline
            "status",
            "source",
            "industry",
            "rating",
            "opportunity_amount",
            "currency",
            "probability",
            "close_date",
            # Address
            "address_line",
            "city",
            "state",
            "postcode",
            "country",
            # Assignment
            "assigned_to",
            "teams",
            # Activity
            "last_contacted",
            "next_follow_up",
            "description",
            # Related
            "contacts",
            "lead_attachment",
            "lead_comments",
            "tags",
            # System
            "created_by",
            "created_at",
            "updated_at",
            "is_active",
            "company_name",
            # Kanban
            "stage",
            "kanban_order",
            # Per-org custom fields (validated via common.custom_fields)
            "custom_fields",
        )


class LeadCreateSerializer(serializers.ModelSerializer):
    probability = serializers.IntegerField(
        max_value=100, required=False, allow_null=True
    )
    opportunity_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    close_date = serializers.DateField(required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        if self.initial_data and self.initial_data.get("status") == "converted":
            self.fields["email"].required = True
        self.fields["first_name"].required = False
        self.fields["last_name"].required = False
        self.fields["salutation"].required = False
        self.org = request_obj.profile.org

    class Meta:
        model = Lead
        fields = (
            # Core Lead Information
            "title",
            "salutation",
            "first_name",
            "last_name",
            "email",
            "phone",
            "job_title",
            "website",
            "linkedin_url",
            # Sales Pipeline
            "status",
            "source",
            "industry",
            "rating",
            "opportunity_amount",
            "currency",
            "probability",
            "close_date",
            # Address
            "address_line",
            "city",
            "state",
            "postcode",
            "country",
            # Activity
            "last_contacted",
            "next_follow_up",
            "description",
            # System
            "company_name",
            "is_active",
        )

    def create(self, validated_data):
        # Default currency from org if not provided and has opportunity_amount
        if not validated_data.get("currency") and validated_data.get(
            "opportunity_amount"
        ):
            request = self.context.get("request")
            if request and hasattr(request, "profile") and request.profile.org:
                validated_data["currency"] = request.profile.org.default_currency
        return super().create(validated_data)


class LeadCreateSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            # Core Lead Information
            "title",
            "salutation",
            "first_name",
            "last_name",
            "email",
            "phone",
            "job_title",
            "website",
            "linkedin_url",
            # Sales Pipeline
            "status",
            "source",
            "industry",
            "rating",
            "opportunity_amount",
            "probability",
            "close_date",
            # Address
            "address_line",
            "city",
            "state",
            "postcode",
            "country",
            # Assignment & Related
            "assigned_to",
            "teams",
            "contacts",
            "tags",
            # Activity
            "last_contacted",
            "next_follow_up",
            "description",
            # System
            "company_name",
        ]


class CreateLeadFromSiteSwaggerSerializer(serializers.Serializer):
    apikey = serializers.CharField()
    title = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone = serializers.CharField()
    email = serializers.CharField()
    source = serializers.CharField()
    description = serializers.CharField()


class LeadDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    lead_attachment = serializers.FileField()


class LeadCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()


class LeadUploadSwaggerSerializer(serializers.Serializer):
    leads_file = serializers.FileField()


# ============================================
# Kanban Serializers
# ============================================


class LeadStageSerializer(serializers.ModelSerializer):
    """Serializer for lead stages."""

    lead_count = serializers.SerializerMethodField()

    class Meta:
        model = LeadStage
        fields = [
            "id",
            "name",
            "order",
            "color",
            "stage_type",
            "maps_to_status",
            "win_probability",
            "wip_limit",
            "lead_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at", "org")

    def get_lead_count(self, obj):
        return obj.leads.count()


class LeadPipelineSerializer(serializers.ModelSerializer):
    """Serializer for lead pipelines with nested stages."""

    stages = LeadStageSerializer(many=True, read_only=True)
    stage_count = serializers.SerializerMethodField()
    lead_count = serializers.SerializerMethodField()

    class Meta:
        model = LeadPipeline
        fields = [
            "id",
            "name",
            "description",
            "is_default",
            "is_active",
            "stages",
            "stage_count",
            "lead_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at", "org")

    def get_stage_count(self, obj):
        return obj.stages.count()

    def get_lead_count(self, obj):
        return Lead.objects.filter(stage__pipeline=obj).count()


class LeadPipelineListSerializer(serializers.ModelSerializer):
    """Simplified pipeline serializer for lists."""

    stage_count = serializers.SerializerMethodField()
    lead_count = serializers.SerializerMethodField()

    class Meta:
        model = LeadPipeline
        fields = [
            "id",
            "name",
            "description",
            "is_default",
            "is_active",
            "stage_count",
            "lead_count",
            "created_at",
        ]

    def get_stage_count(self, obj):
        return obj.stages.count()

    def get_lead_count(self, obj):
        return Lead.objects.filter(stage__pipeline=obj).count()


class LeadKanbanCardSerializer(serializers.ModelSerializer):
    """Lightweight serializer for kanban cards (minimal fields for performance)."""

    assigned_to = ProfileSerializer(read_only=True, many=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = [
            "id",
            "title",
            "full_name",
            "company_name",
            "email",
            "rating",
            "opportunity_amount",
            "currency",
            "status",
            "stage",
            "kanban_order",
            "next_follow_up",
            "is_follow_up_overdue",
            "assigned_to",
            "created_at",
        ]

    def get_full_name(self, obj):
        return str(obj)


class LeadMoveSerializer(serializers.Serializer):
    """Serializer for moving leads in kanban."""

    stage_id = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=LEAD_STATUS, required=False)
    kanban_order = serializers.DecimalField(
        max_digits=15, decimal_places=6, required=False
    )
    above_lead_id = serializers.UUIDField(required=False, allow_null=True)
    below_lead_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        # Must provide either stage_id or status
        if not attrs.get("stage_id") and not attrs.get("status"):
            raise serializers.ValidationError(
                "Either stage_id or status must be provided"
            )
        return attrs
