"""API tests for Phase 4 data-quality endpoints."""

from __future__ import annotations

from rest_framework.test import APITestCase

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.data_quality.models import DuplicateGroup, DuplicateStatus, MergeAudit
from apps.leads.models import EmailStatus, Lead


def _make_pair(email: str = "shared@x.com") -> tuple[Lead, Lead]:
    # Same e-mail is the 100% match signal; we intentionally put the contacts
    # in different companies (and websites) so the detection picks EMAIL rather
    # than a company-level rule.
    c1 = Company.objects.create(name="One Co", website="https://one-a.com")
    contact1 = Contact.objects.create(company=c1, first_name="Jane", email=email)
    lead1 = Lead.objects.create(
        company=c1, contact=contact1, source="test", source_file="one.csv", source_row_number=1,
        email_status=EmailStatus.VALID,
    )
    c2 = Company.objects.create(name="One Co LLC", website="https://one-b.com")
    contact2 = Contact.objects.create(company=c2, first_name="J", email=email.upper())
    lead2 = Lead.objects.create(
        company=c2, contact=contact2, source="test", source_file="two.csv", source_row_number=2,
        email_status=EmailStatus.VALID,
    )
    return lead1, lead2


class DataQualityRootTests(APITestCase):
    def test_ping_returns_ok(self) -> None:
        response = self.client.get("/api/v1/data-quality/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["module"], "data_quality")

    def test_stats_endpoint(self) -> None:
        response = self.client.get("/api/v1/data-quality/stats/")
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        for key in (
            "total_leads",
            "valid_emails",
            "invalid_emails",
            "missing_emails",
            "missing_phones",
            "missing_websites",
            "duplicate_groups",
            "missing_contact_names",
        ):
            self.assertIn(key, stats)


class DuplicateAPITests(APITestCase):
    def test_detect_endpoint(self) -> None:
        _make_pair()
        response = self.client.post("/api/v1/data-quality/duplicates/detect/", {"clear_existing": True}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["EMAIL"], 1)

    def test_list_duplicates(self) -> None:
        _make_pair()
        self.client.post("/api/v1/data-quality/duplicates/detect/", {"clear_existing": True}, format="json")
        response = self.client.get("/api/v1/data-quality/duplicates/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["count"], 1)
        first = response.json()["results"][0]
        self.assertIn("record_a", first)
        self.assertIn("record_b", first)
        self.assertEqual(first["record_a"]["email"], "shared@x.com")

    def test_merge_endpoint(self) -> None:
        lead1, lead2 = _make_pair()
        self.client.post("/api/v1/data-quality/duplicates/detect/", {"clear_existing": True}, format="json")
        group = DuplicateGroup.objects.get(reason_code="EMAIL")
        response = self.client.post(
            f"/api/v1/data-quality/duplicates/{group.pk}/merge/",
            {"winner": lead1.pk, "loser": lead2.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MergeAudit.objects.count(), 1)
        lead2.refresh_from_db()
        self.assertEqual(lead2.lead_status, "MERGED")
        group.refresh_from_db()
        self.assertEqual(group.status, DuplicateStatus.MERGED)

    def test_keep_both_endpoint(self) -> None:
        _make_pair()
        self.client.post("/api/v1/data-quality/duplicates/detect/", {"clear_existing": True}, format="json")
        group = DuplicateGroup.objects.get(reason_code="EMAIL")
        response = self.client.post(
            f"/api/v1/data-quality/duplicates/{group.pk}/keep-both/", {}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        group.refresh_from_db()
        self.assertEqual(group.status, DuplicateStatus.KEPT_BOTH)

    def test_ignore_endpoint(self) -> None:
        _make_pair()
        self.client.post("/api/v1/data-quality/duplicates/detect/", {"clear_existing": True}, format="json")
        group = DuplicateGroup.objects.get(reason_code="EMAIL")
        response = self.client.post(
            f"/api/v1/data-quality/duplicates/{group.pk}/ignore/", {}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        group.refresh_from_db()
        self.assertEqual(group.status, DuplicateStatus.IGNORED)


class MissingEmailAPITests(APITestCase):
    def test_missing_email_list(self) -> None:
        _make_pair()
        c3 = Company.objects.create(name="No Email Inc")
        Lead.objects.create(company=c3, source="seed", email_status=EmailStatus.UNKNOWN)
        response = self.client.get("/api/v1/data-quality/missing-email/")
        self.assertEqual(response.status_code, 200)
        names = {r["company_name"] for r in response.json()["results"]}
        self.assertIn("No Email Inc", names)
