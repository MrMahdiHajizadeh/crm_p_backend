from django.test import TestCase
from django.test.utils import override_settings

from common.models import Org, Profile, User
from common.tasks import set_rls_context
from leads.models import Lead
from leads.tasks import (
    create_lead_from_file,
    send_email,
    send_email_to_assigned_user,
    send_lead_assigned_emails,
)


class TestCeleryTasks(TestCase):
    def setUp(self):
        self.org = Org.objects.create(name="Test Org A")
        set_rls_context(str(self.org.id))

        self.user = User.objects.create_user(email="user1@test.com", password="testpass123")
        self.user1 = User.objects.create_user(email="user2@test.com", password="testpass123")
        self.user2 = User.objects.create_user(email="user3@test.com", password="testpass123")

        self.profile = Profile.objects.create(user=self.user, org=self.org, role="ADMIN", is_active=True)
        self.profile1 = Profile.objects.create(user=self.user1, org=self.org, role="ADMIN", is_active=True)
        self.profile2 = Profile.objects.create(user=self.user2, org=self.org, role="ADMIN", is_active=True)

        self.lead = Lead.objects.create(title="Lead 1", first_name="John", last_name="Doe", email="l1@test.com", org=self.org)
        self.lead1 = Lead.objects.create(title="Lead 2", first_name="Jane", last_name="Doe", email="l2@test.com", org=self.org)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_celery_tasks(self):
        org_id = str(self.lead.org.id)
        task = send_email_to_assigned_user.apply(
            (
                [
                    self.user.id,
                    self.user1.id,
                ],
                self.lead.id,
                org_id,
            ),
        )
        self.assertEqual("SUCCESS", task.state)

        task = send_lead_assigned_emails.apply(
            (
                self.lead.id,
                [
                    self.user.id,
                    self.user1.id,
                    self.user2.id,
                ],
                "https://www.example.com",
                org_id,
            ),
        )
        self.assertEqual("SUCCESS", task.state)

        task = send_email.apply(
            (
                "mail subject",
                "html content",
            ),
            {
                "recipients": [
                    self.user.id,
                    self.user1.id,
                    self.user2.id,
                ],
            },
        )
        self.assertEqual("SUCCESS", task.state)

        org_id1 = str(self.lead1.org.id)
        task = send_lead_assigned_emails.apply(
            (
                self.lead1.id,
                [
                    self.user.id,
                    self.user1.id,
                    self.user2.id,
                ],
                "https://www.example.com",
                org_id1,
            ),
        )
        self.assertEqual("SUCCESS", task.state)

        valid_rows = [
            {
                "title": "lead1 csv",
                "first name": "john",
                "last name": "doe",
                "website": "www.example.com",
                "phone": "911234567890",
                "email": "user1@email.com",
                "address": "address for lead1",
            },
            {
                "title": "lead2 csv",
                "first name": "jane",
                "last name": "doe",
                "website": "www.website.com",
                "phone": "911234567891",
                "email": "user2@email.com",
                "address": "address for lead2",
            },
            {
                "title": "lead3 csv",
                "first name": "joe",
                "last name": "doe",
                "website": "www.test.com",
                "phone": "911234567892",
                "email": "user3@email.com",
                "address": "address for lead3",
            },
            {
                "title": "lead4 csv",
                "first name": "john",
                "last name": "doe",
                "website": "www.sample.com",
                "phone": "911234567893",
                "email": "user4@email.com",
                "address": "address for lead4",
            },
        ]
        invalid_rows = [
            {
                "title": "lead5 csv",
                "first name": "joe",
                "last name": "doe",
                "website": "www.test.com",
                "phone": "911234567892",
                "email": "useremail.com",
                "address": "address for lead3",
            },
            {
                "title": "lead6 csv",
                "first name": "john",
                "last name": "doe",
                "website": "www.sample.com",
                "phone": "911234567893",
                "email": "user4@email",
                "address": "address for lead4",
            },
        ]
        task = create_lead_from_file.apply(
            (valid_rows, invalid_rows, self.profile.id, "example.com", org_id),
        )
        self.assertEqual("SUCCESS", task.state)
