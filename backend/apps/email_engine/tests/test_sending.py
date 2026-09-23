"""Phase 7 SMTP queue, retry, scheduling, and quota tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch

from celery.exceptions import Retry
from django.db import close_old_connections
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.campaigns.models import Campaign, CampaignLead, CampaignStatus
from apps.campaigns.services import transition_campaign
from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.email_engine.models import (
    DailyEmailUsage,
    EmailMessage,
    EmailMessageStatus,
    EmailTemplate,
)
from apps.email_engine.services import reserve_daily_slot
from apps.email_engine.tasks import send_email_message
from apps.leads.models import EmailStatus, Lead


class EmailEngineTestMixin:
    def make_lead(self, index: int) -> Lead:
        company = Company.objects.create(
            name=f"SMTP Company {index}",
            industry="Manufacturing",
            city="Columbus",
            state="OH",
            website=f"https://smtp-{index}.example.com",
        )
        contact = Contact.objects.create(
            company=company,
            first_name=f"First{index}",
            last_name="Recipient",
            email=f"recipient{index}@example.com",
        )
        return Lead.objects.create(
            company=company,
            contact=contact,
            lead_score=80,
            email_status=EmailStatus.VALID,
        )

    def make_message(self, index: int, *, status: str = EmailMessageStatus.QUEUED) -> EmailMessage:
        lead = self.make_lead(index)
        template = EmailTemplate.objects.create(
            name=f"Template {index}",
            subject="Hello",
            body="Hello from OutreachOS.",
        )
        campaign = Campaign.objects.create(
            name=f"Campaign {index}",
            template=template,
            status=CampaignStatus.RUNNING,
        )
        return EmailMessage.objects.create(
            campaign=campaign,
            lead=lead,
            to_email=lead.email,
            subject="Hello",
            body="Hello from OutreachOS.",
            status=status,
            scheduled_at=timezone.now() - timedelta(seconds=1),
        )


class DailyEmailUsageTests(EmailEngineTestMixin, TransactionTestCase):
    def test_89_sent_next_email_is_allowed(self):
        DailyEmailUsage.objects.create(date=timezone.localdate(), sent_count=89, limit=90)
        message = self.make_message(1)

        self.assertTrue(reserve_daily_slot(message))
        usage = DailyEmailUsage.objects.get(date=timezone.localdate())
        self.assertEqual(usage.sent_count, 90)

    def test_90_sent_next_email_is_blocked(self):
        DailyEmailUsage.objects.create(date=timezone.localdate(), sent_count=90, limit=90)
        message = self.make_message(2)

        self.assertFalse(reserve_daily_slot(message))
        self.assertEqual(DailyEmailUsage.objects.get(date=timezone.localdate()).sent_count, 90)

    def test_91st_email_is_impossible(self):
        DailyEmailUsage.objects.create(date=timezone.localdate(), sent_count=90, limit=90)
        messages = [self.make_message(index) for index in range(3, 5)]

        results = [reserve_daily_slot(message) for message in messages]
        self.assertEqual(results, [False, False])
        self.assertEqual(DailyEmailUsage.objects.get(date=timezone.localdate()).sent_count, 90)

    def test_usage_endpoint_exposes_dashboard_safe_quota(self):
        DailyEmailUsage.objects.create(date=timezone.localdate(), sent_count=90, limit=90)

        response = APIClient().get("/api/v1/email/usage/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["sent_today"],
            90,
        )
        self.assertEqual(response.json()["remaining"], 0)
        self.assertNotIn("EMAIL_HOST_PASSWORD", response.json())

    def test_two_workers_cannot_reserve_more_than_one_slot(self):
        """Two workers racing from 89 reservations produce exactly 90."""
        DailyEmailUsage.objects.create(date=timezone.localdate(), sent_count=89, limit=90)
        messages = [self.make_message(index) for index in range(5, 7)]

        def worker(message_id: int) -> bool:
            close_old_connections()
            try:
                message = EmailMessage.objects.get(pk=message_id)
                return reserve_daily_slot(message)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(worker, [message.pk for message in messages]))

        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(DailyEmailUsage.objects.get(date=timezone.localdate()).sent_count, 90)


class QueueAndRetryTests(EmailEngineTestMixin, TransactionTestCase):
    def test_campaign_launch_creates_rendered_spaced_queue(self):
        template = EmailTemplate.objects.create(
            name="Launch template",
            subject="Hello {{first_name}}",
            body="Hello {{contact_name}} at {{company_name}}.",
        )
        campaign = Campaign.objects.create(
            name="Launch campaign",
            template=template,
            sending_start_time="09:00",
            sending_end_time="17:00",
        )
        lead_one = self.make_lead(10)
        lead_two = self.make_lead(11)
        CampaignLead.objects.create(campaign=campaign, lead=lead_one)
        CampaignLead.objects.create(campaign=campaign, lead=lead_two)

        transition_campaign(campaign, CampaignStatus.RUNNING)

        messages = list(EmailMessage.objects.filter(campaign=campaign).order_by("id"))
        self.assertEqual(len(messages), 2)
        self.assertTrue(all(message.status == EmailMessageStatus.QUEUED for message in messages))
        self.assertEqual(messages[0].subject, "Hello First10")
        self.assertNotEqual(messages[0].scheduled_at, messages[1].scheduled_at)
        self.assertTrue(
            CampaignLead.objects.filter(
                campaign=campaign, send_status=CampaignLead.SendStatus.QUEUED
            ).count()
            == 2
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_smtp_failure_retries_and_success_is_not_sent_again(self):
        message = self.make_message(12)

        with patch(
            "apps.email_engine.tasks.deliver_email",
            side_effect=[RuntimeError("SMTP temporarily unavailable"), 1],
        ) as deliver:
            # Task.apply exposes Celery's retry result instead of running the
            # countdown inline. Move the test message due and execute the
            # retry delivery as the worker would.
            with self.assertRaises(Retry):
                send_email_message.apply(args=[message.pk], throw=True)
            message.refresh_from_db()
            message.scheduled_at = timezone.now() - timedelta(seconds=1)
            message.save(update_fields=["scheduled_at"])

            result = send_email_message.apply(args=[message.pk], throw=True)
            self.assertEqual(result.get()["status"], "sent")
            self.assertEqual(deliver.call_count, 2)

            # A redelivered task after a successful SMTP result is a no-op.
            duplicate = send_email_message.apply(args=[message.pk], throw=True)
            self.assertEqual(duplicate.get()["status"], "ignored")
            self.assertEqual(deliver.call_count, 2)

        message.refresh_from_db()
        self.assertEqual(message.status, EmailMessageStatus.SENT)
        self.assertEqual(message.attempt_count, 2)
        self.assertEqual(
            DailyEmailUsage.objects.get(date=timezone.localdate()).sent_count,
            1,
        )
        self.assertEqual(
            CampaignLead.objects.filter(
                campaign=message.campaign,
                lead=message.lead,
                send_status=CampaignLead.SendStatus.SENT,
            ).count(),
            0,
        )
