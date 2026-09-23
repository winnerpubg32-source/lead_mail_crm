"""Phase 5 tests — scoring, activity, detail, bulk actions, CSV export."""

from __future__ import annotations

from django.test import TestCase
from rest_framework.test import APIClient

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.leads.activity_models import LeadActivity, LeadNote
from apps.leads.models import EmailStatus, Lead, LeadStatus
from apps.leads.scoring import POINTS, ScoreClassification, classify_score, compute_lead_score

LIST_URL = "/api/v1/leads/"


class ScoringTests(TestCase):
    def test_full_signal_lead_is_hot(self) -> None:
        company = Company.objects.create(
            name="Acme",
            industry="Manufacturing",
            city="Columbus",
            state="OH",
            website="https://acme.com",
        )
        contact = Contact.objects.create(
            company=company,
            first_name="Jane",
            last_name="Smith",
            email="jane@acme.com",
            phone="614-555-0100",
        )
        lead = Lead.objects.create(
            company=company,
            contact=contact,
            email_status=EmailStatus.VALID,
            lead_status=LeadStatus.NEW,
        )
        lead.refresh_from_db()
        # Valid email(20) + website(15) + contact(10) + phone(10) + industry(10)
        # + location(10) + website_accessible(15) = 90 → HOT.
        self.assertEqual(lead.lead_score, 90)
        self.assertEqual(classify_score(lead.lead_score, lead.email_status), "HOT")

    def test_bounced_email_forces_zero_and_unqualified(self) -> None:
        company = Company.objects.create(name="Acme", industry="Manufacturing", city="C", state="OH")
        contact = Contact.objects.create(company=company, full_name="J", email="j@acme.com", phone="1")
        lead = Lead.objects.create(
            company=company, contact=contact, email_status=EmailStatus.BOUNCED
        )
        lead.refresh_from_db()
        self.assertEqual(lead.lead_score, 0)
        self.assertEqual(classify_score(lead.lead_score, lead.email_status), "UNQUALIFIED")

    def test_classify_thresholds(self) -> None:
        self.assertEqual(classify_score(70, EmailStatus.VALID), "HOT")
        self.assertEqual(classify_score(60, EmailStatus.VALID), "WARM")
        self.assertEqual(classify_score(30, EmailStatus.VALID), "COLD")
        self.assertEqual(classify_score(5, EmailStatus.VALID), "UNQUALIFIED")

    def test_points_config_contract(self) -> None:
        # Spec-locked values so a refactor doesn't silently change scores.
        self.assertEqual(POINTS["valid_email"], 20)
        self.assertEqual(POINTS["website"], 15)
        self.assertEqual(POINTS["website_accessible"], 15)
        self.assertEqual(POINTS["contact"], 10)
        self.assertEqual(POINTS["phone"], 10)
        self.assertEqual(POINTS["invalid_email"], -30)
        self.assertEqual(POINTS["suppressed"], -100)
        self.assertEqual(POINTS["bounced"], -100)
        self.assertEqual(POINTS["unsubscribed"], -100)


class LeadDetailTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.company = Company.objects.create(
            name="Northwind",
            industry="Logistics",
            sub_industry="Freight",
            city="Columbus",
            state="OH",
            street_address="123 Main St",
            zip_code="43215",
            country="US",
            website="https://northwind.com",
        )
        cls.contact = Contact.objects.create(
            company=cls.company,
            first_name="Marcus",
            last_name="Whitfield",
            email="m@northwind.com",
            phone="614-555-0100",
        )
        cls.lead = Lead.objects.create(
            company=cls.company,
            contact=cls.contact,
            lead_score=80,
            lead_status=LeadStatus.QUALIFIED,
            email_status=EmailStatus.VALID,
            source="dataset_import",
        )

    def setUp(self) -> None:
        self.client = APIClient()

    def test_detail_payload_includes_notes_activities_and_breakdown(self) -> None:
        LeadNote.objects.create(lead=self.lead, body="Initial call notes", author="tester")
        LeadActivity.objects.create(
            lead=self.lead,
            activity_type="NOTE_ADDED",
            title="Note added",
            description="Initial call notes",
        )

        response = self.client.get(f"{LIST_URL}{self.lead.pk}/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["company_name"], "Northwind")
        self.assertEqual(body["website"], "https://northwind.com")
        self.assertEqual(body["sub_industry"], "Freight")
        self.assertEqual(body["street_address"], "123 Main St")
        self.assertEqual(body["crm_status"], "QUALIFIED")
        self.assertEqual(len(body["notes"]), 1)
        self.assertEqual(len(body["activities"]), 2)  # CREATED + NOTE_ADDED
        self.assertIn("score_breakdown", body)
        self.assertEqual(body["score_breakdown"]["classification"], "HOT")
        self.assertIn("valid_email", body["score_breakdown"]["components"])

    def test_add_note_records_activity(self) -> None:
        response = self.client.post(
            f"{LIST_URL}{self.lead.pk}/notes/", {"body": "Remember to follow up"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(LeadNote.objects.filter(lead=self.lead).count(), 1)
        self.assertTrue(
            LeadActivity.objects.filter(lead=self.lead, activity_type="NOTE_ADDED").exists()
        )

    def test_rescore_endpoint_recomputes_score(self) -> None:
        self.lead.lead_score = 0
        self.lead.save(update_fields=["lead_score"])
        response = self.client.post(f"{LIST_URL}{self.lead.pk}/rescore/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertGreater(body["lead_score"], 0)
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.lead_score, body["lead_score"])


class BulkActionTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.company = Company.objects.create(name="A", industry="X", city="C", state="OH")
        cls.contact = Contact.objects.create(
            company=cls.company, full_name="P", email="p@a.com", phone="1"
        )
        cls.contact2 = Contact.objects.create(
            company=cls.company, full_name="Q", email="q@a.com", phone="2"
        )
        cls.lead_a = Lead.objects.create(company=cls.company, contact=cls.contact)
        cls.lead_b = Lead.objects.create(company=cls.company, contact=cls.contact2)

    def setUp(self) -> None:
        self.client = APIClient()

    def test_bulk_status_change(self) -> None:
        response = self.client.post(
            f"{LIST_URL}bulk-action/",
            {"ids": [self.lead_a.pk, self.lead_b.pk], "action": "change_status", "lead_status": "QUALIFIED"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["affected"], 2)
        self.lead_a.refresh_from_db()
        self.lead_b.refresh_from_db()
        self.assertEqual(self.lead_a.lead_status, LeadStatus.QUALIFIED)
        self.assertEqual(self.lead_b.lead_status, LeadStatus.QUALIFIED)
        self.assertTrue(
            LeadActivity.objects.filter(
                lead=self.lead_a, activity_type="STATUS_CHANGE"
            ).exists()
        )

    def test_bulk_suppress_sets_do_not_contact(self) -> None:
        response = self.client.post(
            f"{LIST_URL}bulk-action/",
            {"ids": [self.lead_a.pk], "action": "suppress"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.lead_a.refresh_from_db()
        self.assertEqual(self.lead_a.lead_status, LeadStatus.DO_NOT_CONTACT)
        self.assertEqual(self.lead_a.email_status, EmailStatus.SUPPRESSED)
        self.assertEqual(self.lead_a.lead_score, 0)

    def test_csv_export_returns_rows(self) -> None:
        response = self.client.get(f"{LIST_URL}export/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode()
        self.assertIn("company", content)
        self.assertIn("A", content)


class ScoreClassificationFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        company = Company.objects.create(name="A", industry="X", city="C", state="OH")
        for score, email_status in [
            (85, EmailStatus.VALID),    # HOT
            (60, EmailStatus.VALID),    # WARM
            (30, EmailStatus.VALID),    # COLD
            (5, EmailStatus.VALID),     # UNQUALIFIED (low score)
            (80, EmailStatus.BOUNCED),  # UNQUALIFIED (blocked)
        ]:
            contact = Contact.objects.create(
                company=company,
                full_name=f"C{score}",
                email=f"c{score}@a.com",
            )
            Lead.objects.create(
                company=company, contact=contact, lead_score=score, email_status=email_status
            )

    def setUp(self) -> None:
        self.client = APIClient()

    def test_filter_by_classification(self) -> None:
        hot = self.client.get(LIST_URL, {"score_classification": "HOT"}).json()
        self.assertEqual(hot["count"], 1)
        warm = self.client.get(LIST_URL, {"score_classification": "WARM"}).json()
        self.assertEqual(warm["count"], 1)
        cold = self.client.get(LIST_URL, {"score_classification": "COLD"}).json()
        self.assertEqual(cold["count"], 1)
        unq = self.client.get(LIST_URL, {"score_classification": "UNQUALIFIED"}).json()
        self.assertEqual(unq["count"], 2)
