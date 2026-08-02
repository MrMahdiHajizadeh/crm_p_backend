from django.urls import path
from .views import (
    AISettingView,
    AIChatSessionListView,
    AIChatSessionDetailView,
    AIChatMessageView,
)

app_name = "ai_assistant"

urlpatterns = [
    path("settings/", AISettingView.as_view(), name="ai_settings"),
    path("sessions/", AIChatSessionListView.as_view(), name="ai_sessions"),
    path("sessions/<uuid:session_id>/", AIChatSessionDetailView.as_view(), name="ai_session_detail"),
    path("sessions/<uuid:session_id>/message/", AIChatMessageView.as_view(), name="ai_message_create"),
]
