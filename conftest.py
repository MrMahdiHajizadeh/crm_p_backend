"""
Shared pytest fixtures for Django CRM backend tests.

Provides authenticated API clients, test organizations, users, and profiles
that can be reused across all test modules.
"""

import pytest
from django.db import connection
from rest_framework.test import APIClient

from common.models import Org, Profile, User
from common.serializer import OrgAwareRefreshToken


def set_rls_context(org):
    """Set the PostgreSQL RLS session variable for direct ORM operations in tests."""
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.current_org', %s, false)", [str(org.id)]
        )


def clear_rls_context():
    """Clear the PostgreSQL RLS session variable."""
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.current_org', '', false)")


@pytest.fixture(autouse=True)
def _use_db(db):
    """Ensure all tests have database access."""


@pytest.fixture
def org_a():
    org = Org.objects.create(name="Test Organization A")
    set_rls_context(org)
    return org


@pytest.fixture
def org_b():
    org = Org.objects.create(name="Test Organization B")
    set_rls_context(org)
    return org


@pytest.fixture
def admin_user():
    return User.objects.create_user(email="admin@test.com", password="testpass123")


@pytest.fixture
def regular_user():
    return User.objects.create_user(email="user@test.com", password="testpass123")


@pytest.fixture
def user_b():
    return User.objects.create_user(email="userb@test.com", password="testpass123")


@pytest.fixture
def admin_profile(admin_user, org_a):
    set_rls_context(org_a)
    return Profile.objects.get_or_create(
        user=admin_user, org=org_a, defaults={"role": "ADMIN", "is_active": True}
    )[0]


@pytest.fixture
def user_profile(regular_user, org_a):
    set_rls_context(org_a)
    return Profile.objects.get_or_create(
        user=regular_user, org=org_a, defaults={"role": "USER", "is_active": True}
    )[0]


@pytest.fixture
def profile_b(user_b, org_b):
    set_rls_context(org_b)
    return Profile.objects.get_or_create(
        user=user_b, org=org_b, defaults={"role": "ADMIN", "is_active": True}
    )[0]


def _make_authenticated_client(user, org, profile):
    """Create an APIClient with JWT auth for the given user/org."""
    set_rls_context(org)
    client = APIClient()
    token = OrgAwareRefreshToken.for_user_and_org(user, org, profile)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@pytest.fixture
def admin_client(admin_user, org_a, admin_profile):
    return _make_authenticated_client(admin_user, org_a, admin_profile)


@pytest.fixture
def user_client(regular_user, org_a, user_profile):
    return _make_authenticated_client(regular_user, org_a, user_profile)


@pytest.fixture
def org_b_client(user_b, org_b, profile_b):
    return _make_authenticated_client(user_b, org_b, profile_b)


@pytest.fixture
def unauthenticated_client():
    return APIClient()
