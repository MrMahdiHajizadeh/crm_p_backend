from rest_framework import serializers
from .models import AISetting, AIChatSession, AIChatMessage


class AISettingSerializer(serializers.ModelSerializer):
    api_key_masked = serializers.SerializerMethodField()

    class Meta:
        model = AISetting
        fields = (
            "id",
            "api_key",
            "api_key_masked",
            "api_url",
            "model_name",
            "proxy_url",
            "is_active",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "api_key": {"write_only": True, "required": False, "allow_blank": True},
        }

    def get_api_key_masked(self, obj):
        if not obj.api_key:
            return ""
        if len(obj.api_key) <= 8:
            return "••••••••"
        return f"{obj.api_key[:4]}••••••••{obj.api_key[-4:]}"


class AIChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIChatMessage
        fields = (
            "id",
            "session",
            "role",
            "content",
            "reasoning",
            "data_evidence",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class AIChatSessionSerializer(serializers.ModelSerializer):
    messages = AIChatMessageSerializer(many=True, read_only=True)
    messages_count = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    user_phone = serializers.SerializerMethodField()

    class Meta:
        model = AIChatSession
        fields = (
            "id",
            "title",
            "user",
            "user_name",
            "user_phone",
            "created_at",
            "updated_at",
            "messages_count",
            "messages",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_messages_count(self, obj):
        return obj.messages.count()

    def get_user_name(self, obj):
        return obj.user.name if obj.user else "کاربر"

    def get_user_phone(self, obj):
        return obj.user.phone or obj.user.email if obj.user else ""
