"""Lead model tests — defaults, enum vocabulary, derived fields, constraints."""

from __future__ import annotations

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.leads.models import EmailStatus, Lead, LeadStatus


class LeadEnumTests(TestCase):
    def test_lead_status_vocabulary_matches_the_specification(self) -> None:
        self.assertEqual(
            [value for value, _ in LeadStatus.choices],
            [
                "NEW",
                "QUALIFIED",
                "CONTACTED",
                "REPLIED",
                "MEETING",
                "PROPOSAL",
                "WON",
                "LOST",
                "DO_NOT_CONTACT",
            ],
        )

    def test_email_status_vocabulary_matches_the_specification(self) -> None:
        self.assertEqual(
            [value for value, _ in EmailStatus.choices],
            ["UNKNOWN", "VALID", "INVALID", "BOUNCED", "UNSUBSCRIBED", "SUPPRESSED"],
        )


class LeadModelTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(
            name="Northwind Logistics, Inc.",
            industry="Transportation & Logistics",
            city="Columbus",
            state="OH",
            phone="614-555-0100",
        )
        self.contact = Contact.objects.create(
            company=self.company,
            first_name="Marcus",
            last_name="Whitfield",
            job_title="VP Operations",
            email="m.whitfield@northwindlogistics.com",
            phone="614-555-0142",
        )

    def test_defaults(self) -> None:
        lead = Lead.objects.create(company=self.company, contact=self.contact)
        self.assertEqual(lead.lead_score, 0)
        self.assertEqual(lead.lead_status, LeadStatus.NEW)
        self.assertEqual(lead.email_status, EmailStatus.UNKNOWN)
        self.assertEqual(lead.source_file, "")
        self.assertIsNone(lead.source_row_number)

    def test_derived_fields_read_through_relations(self) -> None:
        lead = Lead.objects.create(
            company=self.company,
            contact=self.contact,
            lead_score=92,
            lead_status=LeadStatus.QUALIFIED,
            email_status=EmailStatus.VALID,
        )
        self.assertEqual(lead.company_name, "Northwind Logistics, Inc.")
        self.assertEqual(lead.contact_name, "Marcus Whitfield")
        self.assertEqual(lead.email, "m.whitfield@northwindlogistics.com")
        self.assertEqual(lead.normalized_email, "m.whitfield@northwindlogistics.com")
        self.assertEqual(lead.phone, "614-555-0142")
        self.assertEqual(lead.industry, "Transportation & Logistics")
        self.assertEqual(lead.city, "Columbus")
        self.assertEqual(lead.state, "OH")
        self.assertTrue(lead.is_contactable)

    def test_phone_falls_back_to_company(self) -> None:
        contact = Contact.objects.create(company=self.company, full_name="No Phone")
        lead = Lead.objects.create(company=self.company, contact=contact)
        self.assertEqual(lead.phone, "614-555-0100")

    def test_blocked_email_status_is_not_contactable(self) -> None:
        lead = Lead.objects.create(
            company=self.company, contact=self.contact, email_status=EmailStatus.UNSUBSCRIBED
        )
        self.assertFalse(lead.is_contactable)

    def test_lead_without_relations_has_empty_derived_fields(self) -> None:
        lead = Lead.objects.create()
        self.assertEqual(lead.company_name, "")
        self.assertEqual(lead.contact_name, "")
        self.assertEqual(lead.email, "")
        self.assertFalse(lead.is_contactable)
        self.assertEqual(str(lead), "Lead @ unassigned")

    def test_contact_cannot_have_two_leads_at_the_same_company(self) -> None:
        Lead.objects.create(company=self.company, contact=self.contact)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Lead.objects.create(company=self.company, contact=self.contact)

    def test_company_can_have_multiple_leads_through_different_contacts(self) -> None:
        other = Contact.objects.create(
            company=self.company, full_name="Dana Reed", email="dana@northwindlogistics.com"
        )
        Lead.objects.create(company=self.company, contact=self.contact)
        Lead.objects.create(company=self.company, contact=other)
        self.assertEqual(self.company.leads.count(), 2)

    def test_score_outside_range_is_rejected_by_the_database(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            Lead.objects.create(company=self.company, contact=self.contact, lead_score=101)

    def test_source_provenance_is_stored(self) -> None:
        lead = Lead.objects.create(
            company=self.company,
            contact=self.contact,
            source="dataset_import",
            source_file="us_businesses_q3.csv",
            source_row_number=4287,
        )
        lead.refresh_from_db()
        self.assertEqual(lead.source_file, "us_businesses_q3.csv")
        self.assertEqual(lead.source_row_number, 4287)

    def test_company_deletion_cascades_to_leads(self) -> None:
        Lead.objects.create(company=self.company, contact=self.contact)
        self.company.delete()
        self.assertEqual(Lead.objects.count(), 0)
