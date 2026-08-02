from datetime import datetime, timedelta

from django.test import TestCase
from django.test.utils import override_settings

from accounts.models import Account, AccountEmail
from accounts.tasks import (
    send_email,
    send_email_to_assigned_user,
    send_scheduled_emails,
)


class TestCeleryTasks(TestCase):
    def setUp(self):
        from accounts.models import Account
        from common.models import Org, Profile, User
        from common.tasks import set_rls_context
        from contacts.models import Contact

        self.org = Org.objects.create(name="Test Org")
        set_rls_context(str(self.org.id))

        self.user = User.objects.create_user(email="user1@test.com", password="testpass123")
        self.user1 = User.objects.create_user(email="user2@test.com", password="testpass123")
        self.profile = Profile.objects.create(user=self.user, org=self.org, role="ADMIN", is_active=True)
        self.profile1 = Profile.objects.create(user=self.user1, org=self.org, role="ADMIN", is_active=True)

        self.account = Account.objects.create(name="Test Account", org=self.org, created_by=self.user)
        self.contact = Contact.objects.create(first_name="Test", last_name="Contact", email="c1@test.com", org=self.org)
        self.contact_user1 = Contact.objects.create(first_name="Test2", last_name="Contact2", email="c2@test.com", org=self.org)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_celery_tasks(self):
        org_id = str(self.account.org.id)
        email_scheduled = AccountEmail.objects.create(
            message_subject="message subject",
            message_body="message body",
            from_account=self.account,
            from_email="from@email.com",
            org=self.account.org,
        )
        email_scheduled.recipients.add(self.contact.id, self.contact_user1.id)
        task = send_scheduled_emails.apply()
        self.assertEqual("SUCCESS", task.state)

        task = send_email.apply((email_scheduled.id, org_id))
        self.assertEqual("SUCCESS", task.state)

        task = send_email_to_assigned_user.apply(
            (
                [
                    self.user.id,
                    self.user1.id,
                ],
                self.account.id,
                org_id,
            ),
        )
        self.assertEqual("SUCCESS", task.state)
