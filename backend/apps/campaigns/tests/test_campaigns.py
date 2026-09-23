"""Phase 6 tests — campaigns, templates, wizard transitions."""

from __future__ import annotations

from django.test import TestCase
from rest_framework.test import APIClient

from apps.campaigns.models import Campaign, CampaignLead, CampaignStatus
from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.email_engine.models import EmailTemplate, SAMPLE_LEAD, TEMPLATE_VARIABLES, render_template
from apps.leads.models import EmailStatus, Lead, LeadStatus

CAMPAIGNS_URL = "/api/v1/campaigns/"
TEMPLATES_URL = "/api/v1/email/templates/"


def _make_company(idx: int, **overrides) -> Company:
    defaults = {
        "name": f"Acme {idx}",
        "industry": "Manufacturing",
        "city": "Columbus",
        "state": "OH",
        "website": f"https://acme{idx}.example.com",
    }
    defaults.update(overrides)
    return Company.objects.create(**defaults)


def _make_lead(idx: int, *, company: Company, lead_score: int = 80, email_status=EmailStatus.VALID,
               email: str | None = None) -> Lead:
    contact = Contact.objects.create(
        company=company,
        first_name=f"First{idx}",
        last_name=f"Last{idx}",
        email=email or f"first{idx}@acme{idx}.example.com",
        phone="555-0100",
    )
    return Lead.objects.create(
        company=company, contact=contact, lead_score=lead_score, email_status=email_status
    )


class TemplateTests(TestCase):
    def test_variable_rendering(self) -> None:
        body = "Hi {{first_name}}, welcome to {{company_name}} in {{city}}, {{state}}!"
        rendered = render_template(body, SAMPLE_LEAD)
        self.assertIn("Alex", rendered)
        self.assertIn("Northwind Logistics", rendered)
        self.assertNotIn("{{", rendered)

    def test_unknown_variables_listed(self) -> None:
        tpl = EmailTemplate.objects.create(
            name="T",
            subject="Hi {{first_name}}",
            body="Check {{bogus_var}} and {{company_name}}",
        )
        self.assertIn("bogus_var", tpl.unknown_variables())
        self.assertIn("industry", tpl.missing_variables())

    def test_supported_variables_list_matches_spec(self) -> None:
        self.assertEqual(
            TEMPLATE_VARIABLES,
            ["first_name", "contact_name", "company_name", "industry", "city", "state", "website", "recommended_service"],
        )


class TemplateApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_template_and_preview(self) -> None:
        resp = self.client.post(
            TEMPLATES_URL,
            {
                "name": "Intro",
                "subject": "Quick question for {{company_name}}",
                "body": "Hi {{first_name}}, saw {{company_name}} is in {{industry}}.",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        tpl_id = resp.json()["id"]
        preview = self.client.post(f"{TEMPLATES_URL}{tpl_id}/preview/", {}, format="json").json()
        self.assertIn("Northwind Logistics", preview["subject"])
        self.assertNotIn("{{", preview["body"])

    def test_inline_preview(self) -> None:
        resp = self.client.post(
            f"{TEMPLATES_URL}preview-inline/",
            {"subject": "Hello {{first_name}}", "body": "At {{company_name}}"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Alex", resp.json()["subject"])

    def test_variables_endpoint(self) -> None:
        resp = self.client.get(f"{TEMPLATES_URL}variables/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("supported_variables", resp.json())


class CampaignModelTests(TestCase):
    def test_draft_cannot_launch_without_template(self) -> None:
        c = Campaign.objects.create(name="Test", daily_limit=90)
        from apps.campaigns.services import validate_campaign_for_launch

        errs = validate_campaign_for_launch(c)
        self.assertTrue(any("template" in e for e in errs))

    def test_status_transitions_are_guarded(self) -> None:
        c = Campaign.objects.create(name="T", status=CampaignStatus.DRAFT)
        self.assertTrue(c.can_transition_to(CampaignStatus.READY))
        self.assertFalse(c.can_transition_to(CampaignStatus.COMPLETED))


class CampaignApiTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.co1 = _make_company(1, industry="Manufacturing", city="Columbus", state="OH")
        cls.co2 = _make_company(2, industry="Healthcare", city="Tampa", state="FL")
        cls.lead1 = _make_lead(1, company=cls.co1, lead_score=85)
        cls.lead2 = _make_lead(2, company=cls.co2, lead_score=30)
        cls.tpl = EmailTemplate.objects.create(
            name="Intro", subject="Hi {{first_name}}", body="Hi {{first_name}} at {{company_name}}!"
        )

    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_draft_campaign(self) -> None:
        resp = self.client.post(
            CAMPAIGNS_URL,
            {"name": "Q3 Outreach", "industry": "Manufacturing", "minimum_lead_score": 70, "daily_limit": 60},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["status"], "DRAFT")
        self.assertEqual(resp.json()["daily_limit"], 60)

    def test_list_campaigns(self) -> None:
        Campaign.objects.create(name="A")
        Campaign.objects.create(name="B")
        resp = self.client.get(CAMPAIGNS_URL)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 2)

    def test_prepare_validates_and_snapshots_audience(self) -> None:
        c = Campaign.objects.create(
            name="Q3 MFG", industry="Manufacturing", minimum_lead_score=70, daily_limit=50, template=self.tpl
        )
        resp = self.client.post(f"{CAMPAIGNS_URL}{c.pk}/prepare/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "READY")
        self.assertEqual(body["eligible_count"], 1)  # lead1 (MFG, score 85)
        self.assertEqual(CampaignLead.objects.filter(campaign=c).count(), 1)
        self.assertIn("does not send real e-mails", body["message"])

    def test_preview_audience_returns_matching_leads(self) -> None:
        c = Campaign.objects.create(name="Preview Test", industry="Manufacturing", minimum_lead_score=0)
        resp = self.client.get(f"{CAMPAIGNS_URL}{c.pk}/preview-audience/")
        self.assertEqual(resp.status_code, 200)
        names = {r["company_name"] for r in resp.json()["results"]}
        self.assertIn("Acme 1", names)
        self.assertNotIn("Acme 2", names)

    def test_status_endpoint(self) -> None:
        resp = self.client.get(f"{CAMPAIGNS_URL}statuses/")
        self.assertEqual(resp.status_code, 200)
        labels = {e["value"] for e in resp.json()["campaign_status"]}
        for s in ["DRAFT", "READY", "RUNNING", "PAUSED", "COMPLETED", "CANCELLED"]:
            self.assertIn(s, labels)

    def test_validate_endpoint(self) -> None:
        c = Campaign.objects.create(name="Missing template", daily_limit=90)
        resp = self.client.get(f"{CAMPAIGNS_URL}{c.pk}/validate/")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["valid"])
        self.assertTrue(any("template" in e for e in resp.json()["errors"]))

    def test_running_transition_queues_without_sending_synchronously(self) -> None:
        """Launching queues delivery work; SMTP remains asynchronous and counters start at 0."""
        c = Campaign.objects.create(
            name="Launch", industry="Manufacturing", minimum_lead_score=70, daily_limit=50, template=self.tpl
        )
        resp = self.client.post(f"{CAMPAIGNS_URL}{c.pk}/status/", {"status": "RUNNING"}, format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        body = resp.json()
        self.assertEqual(body["status"], "RUNNING")
        self.assertEqual(body["sent_count"], 0)
        self.assertEqual(body["eligible_count"], 1)
