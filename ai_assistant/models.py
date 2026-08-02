import uuid
from django.db import models
from common.base import BaseModel


class AISetting(BaseModel):
    """
    Organization-level AI configuration settings including API Key, Base URL, Proxy, and Model choice.
    """
    org = models.OneToOneField(
        "common.Org",
        on_delete=models.CASCADE,
        related_name="ai_setting"
    )
    api_key = models.TextField(
        blank=True,
        default="",
        help_text="OpenAI / Gemini / OpenRouter or custom LLM Provider API Key"
    )
    api_url = models.CharField(
        max_length=500,
        default="https://api.openai.com/v1",
        help_text="Base API Endpoint URL (e.g. https://api.openai.com/v1 or custom proxy/local endpoint)"
    )
    model_name = models.CharField(
        max_length=100,
        default="gpt-4o-mini",
        help_text="Target model (e.g. gpt-4o-mini, gpt-4o, gemini-1.5-flash, deepseek-chat)"
    )
    proxy_url = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Optional Proxy URL (e.g. http://127.0.0.1:7890 or socks5://127.0.0.1:1080)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Enable or disable AI Reporting Assistant"
    )

    class Meta:
        db_table = "ai_settings"
        verbose_name = "AI Setting"
        verbose_name_plural = "AI Settings"

    def __str__(self):
        return f"AI Settings for {self.org.name}"


class AIChatSession(BaseModel):
    """
    Chat session history container for an admin user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey(
        "common.Org",
        on_delete=models.CASCADE,
        related_name="ai_chat_sessions"
    )
    user = models.ForeignKey(
        "common.User",
        on_delete=models.CASCADE,
        related_name="ai_chat_sessions"
    )
    title = models.CharField(max_length=255, default="گفتگوی جدید")

    class Meta:
        db_table = "ai_chat_sessions"
        ordering = ("-updated_at",)
        verbose_name = "AI Chat Session"
        verbose_name_plural = "AI Chat Sessions"

    def __str__(self):
        return f"{self.title} ({self.user})"


class AIChatMessage(BaseModel):
    """
    Individual chat messages storing query, AI response, reasoning, and database evidence.
    """
    ROLE_CHOICES = (
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        AIChatSession,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    reasoning = models.TextField(
        blank=True,
        default="",
        help_text="Explanation & logic behind data analysis provided to admins"
    )
    data_evidence = models.JSONField(
        blank=True,
        null=True,
        help_text="Snapshot of database metrics and evidence used by AI"
    )

    class Meta:
        db_table = "ai_chat_messages"
        ordering = ("created_at",)
        verbose_name = "AI Chat Message"
        verbose_name_plural = "AI Chat Messages"

    def __str__(self):
        return f"[{self.role}] {self.content[:30]}..."
