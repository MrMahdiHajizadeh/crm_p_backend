from django.urls import path

from common.views.auth_views import (
    GoogleIdTokenView,
    GoogleOAuthCallbackView,
    MagicLinkRequestView,
    MagicLinkVerifyCodeView,
    MagicLinkVerifyView,
    MeView,
    OrgAwareTokenRefreshView,
    OrgSwitchView,
    PhoneCodeRequestView,
    PhoneCodeVerifyView,
    PhonePasswordLoginView,
)
from common.views.custom_field_views import (
    CustomFieldDefinitionDetailView,
    CustomFieldDefinitionListCreateView,
)
from common.views.dashboard_views import ActivityListView, ApiHomeView
from common.views.notification_views import (
    NotificationDetailView,
    NotificationListView,
    NotificationReadAllView,
    NotificationReadView,
    NotificationStreamView,
)
from common.views.document_views import DocumentDetailView, DocumentListView
from common.views.organization_views import (
    OrgProfileCreateView,
    OrgUpdateView,
    ProfileDetailView,
    ProfileView,
)
from common.views.settings_views import DomainDetailView, DomainList
from common.views.org_settings_views import OrgSettingsView
from common.views.pat_views import (
    PersonalAccessTokenDetailView,
    PersonalAccessTokenListCreateView,
)
from common.views.tags_views import TagsDetailView, TagsListView, TagsRestoreView
from common.views.team_views import TeamsDetailView, TeamsListView
from common.views.user_views import (
    GetTeamsAndUsersView,
    UserDetailView,
    UsersListView,
    UserStatusView,
)

app_name = "api_common"


urlpatterns = [
    path("dashboard/", ApiHomeView.as_view()),
    # JWT Authentication endpoints for SvelteKit integration
    path(
        "auth/refresh-token/",
        OrgAwareTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/profile/", ProfileDetailView.as_view(), name="profile_detail"),
    path("auth/switch-org/", OrgSwitchView.as_view(), name="switch_org"),
    # Magic link (passwordless) authentication
    path("auth/phone-login/", PhonePasswordLoginView.as_view(), name="phone_login"),
    path("auth/magic-link/request/", MagicLinkRequestView.as_view(), name="magic_link_request"),
    path("auth/magic-link/verify/", MagicLinkVerifyView.as_view(), name="magic_link_verify"),
    path("auth/magic-link/verify-code/", MagicLinkVerifyCodeView.as_view(), name="magic_link_verify_code"),
    # OTP phone login (SMS)
    path("auth/request-phone-code/", PhoneCodeRequestView.as_view(), name="request_phone_code"),
    path("auth/verify-phone-code/", PhoneCodeVerifyView.as_view(), name="verify_phone_code"),
    # Organization and profile management
    path("org/", OrgProfileCreateView.as_view()),
    path("org/settings/", OrgSettingsView.as_view(), name="org_settings"),
    path("org/<str:pk>/", OrgUpdateView.as_view()),
    path("profile/", ProfileView.as_view()),
    # Personal Access Tokens (MCP server) — a user manages ONLY their own
    # path(
    #     "profile/tokens/",
    #     PersonalAccessTokenListCreateView.as_view(),
    #     name="pat_list_create",
    # ),
    # path(
    #     "profile/tokens/<uuid:pk>/",
    #     PersonalAccessTokenDetailView.as_view(),
    #     name="pat_detail",
    # ),
    # User management
    path("users/get-teams-and-users/", GetTeamsAndUsersView.as_view()),
    path("users/", UsersListView.as_view()),
    path("user/<str:pk>/", UserDetailView.as_view()),
    path("user/<str:pk>/status/", UserStatusView.as_view()),
    # Documents
    path("documents/", DocumentListView.as_view()),
    # Activities (for dashboard recent activities)
    path("activities/", ActivityListView.as_view(), name="activities"),
    # Teams (merged from teams app)
    path("teams/", TeamsListView.as_view()),
    path("teams/<str:pk>/", TeamsDetailView.as_view()),
    # Tags
    path("tags/", TagsListView.as_view()),
    path("tags/<str:pk>/", TagsDetailView.as_view()),
    path("tags/<str:pk>/restore/", TagsRestoreView.as_view()),
    # Custom fields (per-org schema extension; cross-entity)
    # path(
    #     "custom-fields/",
    #     CustomFieldDefinitionListCreateView.as_view(),
    #     name="custom_fields_list_create",
    # ),
    # path(
    #     "custom-fields/<str:pk>/",
    #     CustomFieldDefinitionDetailView.as_view(),
    #     name="custom_field_detail",
    # ),
    # In-app notifications (per-recipient feed)
    path("notifications/", NotificationListView.as_view(), name="notifications_list"),
    path(
        "notifications/stream/",
        NotificationStreamView.as_view(),
        name="notifications_stream",
    ),
    path(
        "notifications/read-all/",
        NotificationReadAllView.as_view(),
        name="notifications_read_all",
    ),
    path(
        "notifications/<str:pk>/read/",
        NotificationReadView.as_view(),
        name="notifications_read",
    ),
    path(
        "notifications/<str:pk>/",
        NotificationDetailView.as_view(),
        name="notifications_detail",
    ),
]
