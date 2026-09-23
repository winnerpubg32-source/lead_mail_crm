"""Tests for the development seed command (``manage.py seed_lead_data``)."""

from __future__ import annotations

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.leads.models import Lead


def run_seed(**options) -> str:
    out = StringIO()
    call_command("seed_lead_data", stdout=out, **options)
    return out.getvalue()


class SeedCommandTests(TestCase):
    def test_seeds_a_connected_dataset(self) -> None:
        run_seed(companies=6, leads_per_company=2, seed=7)

        self.assertEqual(Company.objects.count(), 6)
        self.assertGreaterEqual(Contact.objects.count(), 6)
        self.assertGreaterEqual(Lead.objects.count(), 6)

        # Every lead is wired to a real company and contact.
        for lead in Lead.objects.select_related("company", "contact"):
            self.assertIsNotNone(lead.company_id)
            self.assertIsNotNone(lead.contact_id)
            self.assertEqual(lead.contact.company_id, lead.company_id)

    def test_generated_data_respects_model_rules(self) -> None:
        run_seed(companies=10, leads_per_company=2, seed=11)

        # Normalised fields are populated, scores stay inside the allowed range.
        self.assertEqual(Company.objects.filter(normalized_name="").count(), 0)
        self.assertEqual(Company.objects.filter(normalized_website="").count(), 0)
        self.assertEqual(Lead.objects.filter(lead_score__gt=100).count(), 0)
        self.assertEqual(Lead.objects.filter(lead_score__lt=0).count(), 0)

        # Job titles stay industry appropriate (dental groups have no plant directors).
        for contact in Contact.objects.select_related("company"):
            if contact.company and contact.company.industry == "Healthcare":
                self.assertNotIn("Plant Director", contact.job_title)

    def test_seed_is_deterministic_for_a_given_seed(self) -> None:
        run_seed(companies=5, leads_per_company=1, seed=99, flush=True)
        first = list(Company.objects.order_by("id").values_list("name", flat=True))
        first_leads = list(Lead.objects.order_by("id").values_list("lead_score", flat=True))

        run_seed(companies=5, leads_per_company=1, seed=99, flush=True)
        second = list(Company.objects.order_by("id").values_list("name", flat=True))
        second_leads = list(Lead.objects.order_by("id").values_list("lead_score", flat=True))

        self.assertEqual(first, second)
        self.assertEqual(first_leads, second_leads)

    def test_flush_removes_existing_rows_before_seeding(self) -> None:
        run_seed(companies=4, leads_per_company=1, seed=3)
        run_seed(companies=2, leads_per_company=1, seed=3, flush=True)
        self.assertEqual(Company.objects.count(), 2)

    def test_empty_flag_only_clears_the_database(self) -> None:
        run_seed(companies=4, leads_per_company=2, seed=5)
        output = run_seed(flush=True, empty=True)

        self.assertEqual(Company.objects.count(), 0)
        self.assertEqual(Contact.objects.count(), 0)
        self.assertEqual(Lead.objects.count(), 0)
        self.assertIn("empty", output.lower())

    def test_every_status_and_source_is_represented_at_scale(self) -> None:
        run_seed(companies=45, leads_per_company=2, seed=20260923)

        statuses = set(Lead.objects.values_list("lead_status", flat=True))
        # The seed uses a weighted distribution; at this size every status appears.
        self.assertEqual(len(statuses), 9)

        with_source_file = Lead.objects.exclude(source_file="")
        self.assertGreater(with_source_file.count(), 0)
        for lead in with_source_file[:20]:
            self.assertIsNotNone(lead.source_row_number)
