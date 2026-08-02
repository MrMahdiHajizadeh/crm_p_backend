from django.test import TestCase
from django.test.utils import override_settings

from contacts.tasks import send_email_to_assigned_user


class TestCeleryTasks(TestCase):
    def setUp(self):
        from common.models import Org, Profile, User
        from common.tasks import set_rls_context
        from contacts.models import Contact

        self.org = Org.objects.create(name="Test Org")
        set_rls_context(str(self.org.id))

        self.user = User.objects.create_user(email="user1@test.com", password="testpass123")
        self.user_contacts_mp = User.objects.create_user(email="user2@test.com", password="testpass123")
        self.profile = Profile.objects.create(user=self.user, org=self.org, role="ADMIN", is_active=True)
        self.profile2 = Profile.objects.create(user=self.user_contacts_mp, org=self.org, role="ADMIN", is_active=True)

        self.contact = Contact.objects.create(first_name="Test", last_name="Contact", email="c1@test.com", org=self.org)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_celery_tasks(self):
        org_id = str(self.contact.org.id)
        task = send_email_to_assigned_user.apply(
            (
                [
                    self.profile.id,
                    self.profile2.id,
                ],
                self.contact.id,
                org_id,
            ),
        )
        self.assertEqual("SUCCESS", task.state)
