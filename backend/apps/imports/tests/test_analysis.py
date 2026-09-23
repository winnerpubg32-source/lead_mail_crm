"""Preview analysis: the counts shown before the user confirms an import."""

from __future__ import annotations

import tempfile
from pathlib import Path

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.imports.analysis import PREVIEW_ROWS, analyze_file, describe_file
from apps.imports.records import MappingError
from apps.imports.tests.factories import write_csv, write_xlsx

HEADERS = ["Business Name", "Contact", "E-mail", "Website", "City"]
MAPPING = {
    "Business Name": "company_name",
    "Contact": "contact_name",
    "E-mail": "email",
    "Website": "website",
    "City": "city",
}


class AnalysisTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def analyse(self, rows, name="leads.csv", mapping=MAPPING, **kwargs):
        path = write_csv(self.tmp / name, rows, **kwargs)
        return analyze_file(path, file_type="csv", mapping=mapping)


class CountTests(AnalysisTestCase):
    def test_counts_rows_emails_and_invalid_addresses(self):
        result = self.analyse(
            [
                HEADERS,
                ["Acme Ltd", "Jane", "jane@acme.com", "acme.com", "Austin"],
                ["Beta Corp", "Bob", "bob@beta.com", "beta.com", "Reno"],
                ["No Mail Co", "Ann", "", "nomail.com", "Boise"],
                ["Bad Mail Co", "Sid", "sid[at]example.com", "bad.com", "Tulsa"],
            ]
        )
        self.assertEqual(result.total_rows, 4)
        self.assertEqual(result.rows_with_email, 2)
        self.assertEqual(result.rows_without_email, 2)
        self.assertEqual(result.invalid_emails, 1)
        self.assertEqual(result.potential_duplicates, 0)

    def test_sample_rows_are_capped(self):
        rows = [HEADERS]
        rows.extend(
            [f"Company {i}", "Person", f"p{i}@example.com", f"company{i}.com", "Austin"]
            for i in range(PREVIEW_ROWS + 25)
        )

        result = self.analyse(rows)
        self.assertEqual(result.total_rows, PREVIEW_ROWS + 25)
        self.assertEqual(len(result.sample_rows), PREVIEW_ROWS)
        self.assertEqual(result.sample_rows[0]["row"], 2)

    def test_file_without_a_header_row_is_rejected(self):
        path = write_csv(self.tmp / "empty.csv", [])
        with self.assertRaises(MappingError):
            analyze_file(path, file_type="csv", mapping={})


class DuplicateDetectionTests(AnalysisTestCase):
    def test_duplicates_inside_the_file_are_counted(self):
        result = self.analyse(
            [
                HEADERS,
                ["Acme Ltd", "Jane", "jane@acme.com", "acme.com", "Austin"],
                ["Acme Ltd", "Jane", "jane@acme.com", "acme.com", "Austin"],
                ["Beta Corp", "Bob", "bob@beta.com", "beta.com", "Reno"],
            ]
        )
        self.assertEqual(result.potential_duplicates, 1)

    def test_duplicates_against_the_database_are_counted(self):
        company = Company.objects.create(name="Acme Ltd", website="acme.com")
        Contact.objects.create(company=company, full_name="Jane Doe", email="jane@acme.com")

        result = self.analyse(
            [
                HEADERS,
                ["Acme Ltd", "Jane", "jane@acme.com", "acme.com", "Austin"],
                ["Other Co", "Ann", "ann@other.com", "other.com", "Boise"],
            ]
        )
        self.assertEqual(result.potential_duplicates, 1)

    def test_domain_match_counts_even_with_a_new_address(self):
        Company.objects.create(name="Acme Ltd", website="https://www.acme.com/about")

        result = self.analyse(
            [HEADERS, ["Acme Ltd", "New Person", "new@acme.com", "acme.com", "Austin"]]
        )
        self.assertEqual(result.potential_duplicates, 1)

    def test_a_match_on_the_company_name_alone_is_not_a_duplicate(self):
        # Name-only matches are still imported (the importer merges them), but
        # the preview only claims a duplicate when the e-mail or domain matches.
        Company.objects.create(name="Acme Ltd")

        result = self.analyse(
            [HEADERS, ["Acme Ltd", "Jane", "jane@acme.com", "acme.com", "Austin"]]
        )
        self.assertEqual(result.potential_duplicates, 0)


class ScaleTests(AnalysisTestCase):
    def test_duplicate_lookups_are_batched_not_per_row(self):
        """3 000 rows must not cost 3 000 queries."""
        rows = [HEADERS]
        rows.extend(
            [f"Company {i}", f"Person {i}", f"p{i}@example.com", f"company{i}.com", "Austin"]
            for i in range(3000)
        )
        path = write_csv(self.tmp / "big.csv", rows)

        with CaptureQueriesContext(connection) as queries:
            result = analyze_file(path, file_type="csv", mapping=MAPPING)

        # 3 000 rows / 1 000 per batch = three blocks with two lookups each.
        # A per-row lookup would be 3 000+ queries; the ceiling below is generous
        # so the test fails only if the batching is broken.
        self.assertLess(len(queries), 20, [q["sql"][:80] for q in queries.captured_queries])

        self.assertEqual(result.total_rows, 3000)
        self.assertEqual(result.rows_with_email, 3000)
        self.assertEqual(len(result.sample_rows), PREVIEW_ROWS)

    def test_in_file_duplicates_are_tracked_beyond_the_sample(self):
        rows = [HEADERS]
        rows.extend(
            [f"Company {i}", f"Person {i}", f"p{i}@example.com", f"company{i}.com", "Austin"]
            for i in range(60)
        )
        rows.append(["Company 0", "Person 0", "p0@example.com", "company0.com", "Austin"])

        result = self.analyse(rows)
        self.assertEqual(result.total_rows, 61)
        self.assertEqual(result.potential_duplicates, 1)
        self.assertEqual(len(result.sample_rows), PREVIEW_ROWS)


class MappingPayloadTests(AnalysisTestCase):
    def test_mapping_uses_the_canonical_column_to_field_shape(self):
        result = self.analyse(
            [HEADERS, ["Acme Ltd", "Jane", "jane@acme.com", "acme.com", "Austin"]]
        )

        self.assertEqual(
            result.mapping,
            {
                "Business Name": "company_name",
                "Contact": "contact_name",
                "E-mail": "email",
                "Website": "website",
                "City": "city",
            },
        )
        self.assertTrue(all("field" in column for column in result.columns))

    def test_unmapped_columns_are_present_with_none(self):
        rows = [["Business Name", "Favourite Colour"], ["Acme Ltd", "blue"]]
        result = self.analyse(rows, mapping={"Business Name": "company_name"})

        self.assertEqual(
            result.mapping, {"Business Name": "company_name", "Favourite Colour": None}
        )

    def test_remapping_changes_the_numbers(self):
        rows = [
            ["Company", "Owner", "E-mail"],
            ["Acme Ltd", "Jane", "jane@acme.com"],
            ["Beta Corp", "Bob", "bob@beta.com"],
        ]
        auto = self.analyse(rows, mapping={})
        self.assertEqual(auto.rows_with_email, 2)

        without_email = self.analyse(
            rows, mapping={"Company": "company_name", "Owner": "contact_name"}
        )
        self.assertEqual(without_email.rows_with_email, 0)
        self.assertEqual(without_email.rows_without_email, 2)


class DescribeFileTests(AnalysisTestCase):
    def test_csv_metadata(self):
        path = write_csv(self.tmp / "leads.csv", [HEADERS], delimiter=";")
        info = describe_file(path, "csv")
        self.assertEqual(info["file_type"], "csv")
        self.assertEqual(info["delimiter"], ";")
        self.assertEqual(info["sheets"], [])

    def test_xlsx_metadata_lists_sheets(self):
        path = write_xlsx(self.tmp / "book.xlsx", {"Leads": [HEADERS], "Lookups": [["Industry"]]})
        info = describe_file(path, "xlsx")
        self.assertEqual(info["sheets"], ["Leads", "Lookups"])
        self.assertEqual(info["file_type"], "xlsx")
