"""Tests for duplicate detection, merge logic and data-quality services."""

from __future__ import annotations

from django.test import TestCase

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.data_quality.models import DuplicateGroup, DuplicateStatus, MergeAudit
from apps.data_quality.services import (
    compute_data_quality_stats,
    detect_duplicates,
    find_missing_email_leads,
    ignore_group,
    keep_both_group,
    merge_leads,
)
from apps.leads.models import EmailStatus, Lead, LeadStatus


def make_lead(
    *,
    company_name: str = "Acme Inc",
    website: str = "",
    company_phone: str = "",
    address: str = "",
    city: str = "",
    state: str = "",
    industry: str = "",
    contact_first: str = "",
    contact_last: str = "",
    email: str = "",
    phone: str = "",
    source: str = "test",
    source_file: str = "test.csv",
    source_row: int | None = None,
):
    """Helper to create a full company/contact/lead triple for tests."""
    company = Company.objects.create(
        name=company_name,
        website=website,
        phone=company_phone,
        street_address=address,
        city=city,
        state=state,
        industry=industry,
        source=source,
    )
    contact = None
    if contact_first or contact_last or email or phone:
        contact = Contact.objects.create(
            company=company,
            first_name=contact_first,
            last_name=contact_last,
            email=email,
            phone=phone,
        )
    return Lead.objects.create(
        company=company,
        contact=contact,
        source=source,
        source_file=source_file,
        source_row_number=source_row,
        email_status=EmailStatus.VALID if email else EmailStatus.UNKNOWN,
    )


class DuplicateDetectionTests(TestCase):
    def test_email_match_confidence_100(self) -> None:
        make_lead(company_name="A Co", contact_first="Jane", email="jane@acme.com", source_row=1)
        make_lead(company_name="B Co", contact_first="J", email="JANE@acme.com ", source_row=2)
        result = detect_duplicates()
        self.assertEqual(result["EMAIL"], 1)
        group = DuplicateGroup.objects.get(reason_code="EMAIL")
        self.assertEqual(group.confidence, 100)
        self.assertEqual(group.members.count(), 2)

    def test_company_website_match(self) -> None:
        # Same website => same company (enforced by unique constraint); two
        # leads attached to that company with different contacts are the pair.
        company = Company.objects.create(name="Acme", website="https://acme.com")
        contact_a = Contact.objects.create(company=company, first_name="Jane", email="jane@acme.com")
        contact_b = Contact.objects.create(company=company, first_name="Bob", email="bob@acme.com")
        Lead.objects.create(company=company, contact=contact_a, source="test", email_status=EmailStatus.VALID)
        Lead.objects.create(company=company, contact=contact_b, source="test", email_status=EmailStatus.VALID)
        result = detect_duplicates(clear_existing=True)
        self.assertEqual(result["COMPANY_WEBSITE"], 1)
        group = DuplicateGroup.objects.get(reason_code="COMPANY_WEBSITE")
        self.assertEqual(group.confidence, 95)

    def test_company_phone_match(self) -> None:
        # Two different formatting variations for the same domestic number.
        make_lead(
            company_name="Acme",
            company_phone="(614) 555-0142",
            contact_first="A",
            email="a@x.com",
            website="https://acme-a.com",
        )
        make_lead(
            company_name="Acme Inc",
            company_phone="614.555.0142",
            contact_first="B",
            email="b@x.com",
            website="https://acme-b.com",
        )
        result = detect_duplicates(clear_existing=True)
        self.assertEqual(result["COMPANY_PHONE"], 1)

    def test_company_address_match(self) -> None:
        make_lead(
            company_name="Acme",
            address="123 Main Street",
            city="Columbus",
            state="OH",
            contact_first="A",
            email="a@x.com",
            website="https://acme-a.com",
        )
        make_lead(
            company_name="Acme LLC",
            address="123 Main St.",
            city="columbus",
            state="ohio",
            contact_first="B",
            email="b@x.com",
            website="https://acme-b.com",
        )
        result = detect_duplicates(clear_existing=True)
        self.assertEqual(result["COMPANY_ADDRESS"], 1)

    def test_company_city_state_match(self) -> None:
        # Same company name + city + state but different street addresses.
        make_lead(
            company_name="Acme",
            city="Columbus",
            state="OH",
            address="100 Main St",
            contact_first="A",
            email="a@x.com",
            website="https://acme-a.com",
        )
        make_lead(
            company_name="ACME LLC",
            city="Columbus",
            state="OH",
            address="200 Oak Avenue",
            contact_first="B",
            email="b@x.com",
            website="https://acme-b.com",
        )
        result = detect_duplicates(clear_existing=True)
        self.assertEqual(result["COMPANY_CITY_STATE"], 1)

    def test_same_pair_not_duplicated_on_rerun(self) -> None:
        make_lead(company_name="X", contact_first="Jane", email="same@x.com")
        make_lead(company_name="Y", contact_first="Jan", email="same@x.com")
        detect_duplicates()
        detect_duplicates()
        self.assertEqual(DuplicateGroup.objects.count(), 1)

    def test_clear_existing_resets(self) -> None:
        make_lead(company_name="X", contact_first="Jane", email="same@x.com")
        make_lead(company_name="Y", contact_first="Jan", email="same@x.com")
        detect_duplicates()
        self.assertEqual(DuplicateGroup.objects.count(), 1)
        detect_duplicates(clear_existing=True)
        self.assertEqual(DuplicateGroup.objects.count(), 1)


class MergeTests(TestCase):
    def _make_pair(self):
        winner = make_lead(
            company_name="Winner Co",
            website="https://winner.com",
            company_phone="",
            address="",
            city="Columbus",
            state="OH",
            industry="Software",
            contact_first="Jane",
            contact_last="",
            email="jane@winner.com",
            phone="",
            source_file="winners.csv",
            source_row=1,
        )
        loser = make_lead(
            company_name="Winner Co LLC",
            website="",
            company_phone="(614) 555-0142",
            address="123 Main St",
            city="Columbus",
            state="OH",
            industry="",
            contact_first="Jane",
            contact_last="Smith",
            email="jane@winner.com",
            phone="614-555-0199",
            source_file="losers.csv",
            source_row=2,
        )
        return winner, loser

    def test_merge_preserves_provenance(self) -> None:
        winner, loser = self._make_pair()
        detect_duplicates()
        group = DuplicateGroup.objects.first()
        audit = merge_leads(winner.pk, loser.pk, group=group, performed_by="test")
        self.assertEqual(audit.surviving_lead_id, winner.pk)
        self.assertEqual(audit.merged_lead_id, loser.pk)

        loser.refresh_from_db()
        winner.refresh_from_db()
        self.assertEqual(loser.lead_status, LeadStatus.MERGED)
        self.assertEqual(loser.merged_into_id, winner.pk)
        self.assertEqual(loser.source_file, "losers.csv")
        self.assertEqual(loser.source_row_number, 2)
        self.assertEqual(winner.source_file, "winners.csv")
        self.assertEqual(winner.source_row_number, 1)

    def test_merge_fills_empty_company_fields(self) -> None:
        winner, loser = self._make_pair()
        merge_leads(winner.pk, loser.pk)
        winner.refresh_from_db()
        winner.company.refresh_from_db()
        self.assertEqual(winner.company.phone, "(614) 555-0142")
        self.assertEqual(winner.company.street_address, "123 Main St")

    def test_merge_fills_empty_contact_fields(self) -> None:
        winner, loser = self._make_pair()
        merge_leads(winner.pk, loser.pk)
        winner.refresh_from_db()
        winner.contact.refresh_from_db()
        self.assertEqual(winner.contact.last_name, "Smith")

    def test_audit_records_source(self) -> None:
        winner, loser = self._make_pair()
        audit = merge_leads(winner.pk, loser.pk)
        sources = {s["source_file"] for s in audit.merged_sources}
        self.assertEqual(sources, {"winners.csv", "losers.csv"})

    def test_merge_rejects_self_merge(self) -> None:
        winner, _ = self._make_pair()
        with self.assertRaises(ValueError):
            merge_leads(winner.pk, winner.pk)

    def test_merge_is_transactional(self) -> None:
        # Ensures MergeAudit exists after merge.
        winner, loser = self._make_pair()
        merge_leads(winner.pk, loser.pk)
        self.assertEqual(MergeAudit.objects.count(), 1)


class WorkflowActionTests(TestCase):
    def test_ignore_marks_group(self) -> None:
        make_lead(company_name="A", contact_first="X", email="same@x.com")
        make_lead(company_name="B", contact_first="Y", email="same@x.com")
        detect_duplicates()
        group = DuplicateGroup.objects.get()
        ignore_group(group.pk)
        group.refresh_from_db()
        self.assertEqual(group.status, DuplicateStatus.IGNORED)

    def test_keep_both_marks_group(self) -> None:
        make_lead(company_name="A", contact_first="X", email="same@x.com")
        make_lead(company_name="B", contact_first="Y", email="same@x.com")
        detect_duplicates()
        group = DuplicateGroup.objects.get()
        keep_both_group(group.pk)
        group.refresh_from_db()
        self.assertEqual(group.status, DuplicateStatus.KEPT_BOTH)


class MissingEmailTests(TestCase):
    def test_filters_leads_without_email(self) -> None:
        make_lead(company_name="Has Email", contact_first="A", email="a@x.com")
        make_lead(company_name="No Email", contact_first="", email="")
        make_lead(company_name="No Contact", city="Columbus")
        qs = find_missing_email_leads()
        companies = {lead.company.name for lead in qs}
        self.assertEqual(companies, {"No Email", "No Contact"})

    def test_excludes_merged(self) -> None:
        winner = make_lead(company_name="W", contact_first="W", email="w@x.com")
        loser = make_lead(company_name="L")
        merge_leads(winner.pk, loser.pk)
        qs = find_missing_email_leads()
        # Loser is MERGED so not in list; winner has email so not in list.
        self.assertEqual(qs.count(), 0)


class StatsTests(TestCase):
    def test_stats_counts(self) -> None:
        make_lead(company_name="A", contact_first="a", email="a@x.com")
        make_lead(company_name="B")
        lead_invalid = Lead.objects.get(company__name="B")
        lead_invalid.email_status = EmailStatus.INVALID
        lead_invalid.save()
        stats = compute_data_quality_stats()
        self.assertEqual(stats["total_leads"], 2)
        self.assertEqual(stats["valid_emails"], 1)
        self.assertEqual(stats["invalid_emails"], 1)
        self.assertEqual(stats["missing_emails"], 1)
