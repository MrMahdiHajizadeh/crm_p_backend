from django.test import TestCase
from django.test.utils import override_settings

from cases.models import Case
from cases.tasks import send_email_to_assigned_user


class TestCeleryTasks(TestCase):
    def setUp(self):
        from common.models import Org, Profile, User
        from common.tasks import set_rls_context

        self.org = Org.objects.create(name="Test Org")
        set_rls_context(str(self.org.id))

        self.user = User.objects.create_user(email="user1@test.com", password="testpass123")
        self.user1 = User.objects.create_user(email="user2@test.com", password="testpass123")
        self.profile = Profile.objects.create(user=self.user, org=self.org, role="ADMIN", is_active=True)
        self.profile1 = Profile.objects.create(user=self.user1, org=self.org, role="ADMIN", is_active=True)

        self.case = Case.objects.create(name="Test Case", org=self.org)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_celery_tasks(self):
        org_id = str(self.case.org.id)
        task = send_email_to_assigned_user.apply(
            (
                [
                    self.profile.id,
                    self.profile1.id,
                ],
                self.case.id,
                org_id,
            ),
        )
        self.assertEqual("SUCCESS", task.state)
