from django.urls import path

from leads.views.lead_interactions import (
    CreateLeadFromSite,
    FollowUpListView,
    InteractionLogDetailView,
    LeadAttachmentView,
    LeadCommentView,
    LeadInteractionListCreateView,
    LeadScopedInteractionView,
    LeadUploadView,
)
from leads.views.lead_views import LeadDetailView, LeadListView
from leads.views.kanban_views import (
    LeadKanbanView,
    LeadMoveView,
    LeadPipelineListCreateView,
    LeadPipelineDetailView,
    LeadStageCreateView,
    LeadStageDetailView,
    LeadStageReorderView,
)

app_name = "api_leads"

urlpatterns = [
    # Lead list and bulk operations
    path("", LeadListView.as_view()),
    # Global interactions (not scoped to a specific lead)
    path("interactions/", LeadInteractionListCreateView.as_view(), name="interaction_list_create"),
    path("interactions/<str:pk>/", InteractionLogDetailView.as_view(), name="interaction_detail"),
    # Follow-ups (unified across all entities)
    path("follow-ups/", FollowUpListView.as_view(), name="follow_up_list"),
    # Kanban endpoints
    path("kanban/", LeadKanbanView.as_view(), name="lead_kanban"),
    # Lead-scoped interactions
    path("<str:pk>/interactions/", LeadScopedInteractionView.as_view(), name="lead_interactions"),
    # Lead detail routes (must be after specific routes due to pk pattern)
    path("<str:pk>/", LeadDetailView.as_view()),
    path("<str:pk>/move/", LeadMoveView.as_view(), name="lead_move"),
    path("comment/<str:pk>/", LeadCommentView.as_view()),
    path("attachment/<str:pk>/", LeadAttachmentView.as_view()),
]
