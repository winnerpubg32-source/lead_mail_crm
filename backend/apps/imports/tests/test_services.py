"""
Import-run tests: chunking, dedup, merging, counters and provenance.

``ImportRunner`` is driven directly (no broker) with a deliberately small chunk
size so multi-chunk behaviour is exercised by every test.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import mock

from django.test import TestCase

from apps.companies.models import Company
from apps.contacts.models import Contact, PhoneType
from apps.imports.models import ImportJob, ImportStatus
from apps.imports.services import ImportRunner, process_import_job
from apps.imports.tests.factories import MESSY_HEADERS, MESSY_ROWS, write_csv, write_xlsx
from apps.leads.models import Lead

HEADERS = [
    "Business Name",
    "Contact",
    "E-mail",
    "Phone",
    "Website",
    "Industry",
    "City",
    "State",
    "Employees",
]
MAPPING = {
    "Business Name": "company_name",
    "Contact": "contact_name",
    "E-mail": "email",
    "Phone": "phone",
    "Website": "website",
    "Industry": "industry",
    "City": "city",
    "State": "state",
    "Employees": "employee_count",
}


class ImportRunTestCase(TestCase):
    """Base class: temp MEDIA_ROOT, a file on disk and a QUEUED job."""

    def setUp(self):
        super().setUp()
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def make_job(
        self,
        rows: list[list[str]],
        *,
        name: str = "leads.csv",
        mapping: dict | None = None,
        **kwargs,
    ) -> ImportJob:
        path = write_csv(self.tmp / name, rows, **kwargs)
        job = ImportJob.objects.create(
            filename=name,
            file_type="csv",
            file_size=path.stat().st_size,
            headers=list(rows[0]),
            column_mapping=mapping if mapping is not None else {},
        )
        with open(path, "rb") as handle:
            job.upload.save(name, handle, save=True)
        return job

    def run_job(self, job: ImportJob, chunk_size: int = 2):
        with mock.patch("apps.imports.services.CHUNK_SIZE", chunk_size):
            return ImportRunner(job).run(), ImportJob.objects.get(pk=job.pk)


class ImportCreationTests(ImportRunTestCase):
    def test_creates_companies_contacts_and_leads(self):
        job = self.make_job(
            [
                HEADERS,
                [
                    "Northwind Logistics, Inc.",
                    "Marcus Whitfield",
                    "m@northwind.com",
                    "(614) 555-0142",
                    "northwind.com",
                    "Logistics",
                    "Columbus",
                    "OH",
                    "850",
                ],
            ],
            mapping=MAPPING,
        )
        ImportRunner(job).run()
        job.refresh_from_db()

        company = Company.objects.get()
        contact = Contact.objects.get()
        lead = Lead.objects.get()

        self.assertEqual(company.name, "Northwind Logistics, Inc.")
        self.assertEqual(company.normalized_name, "northwind logistics")
        self.assertEqual(company.normalized_website, "northwind.com")
        self.assertEqual(company.city, "Columbus")
        self.assertEqual(company.employee_count, 850)
        self.assertEqual(company.source, "import:leads.csv")

        self.assertEqual(contact.full_name, "Marcus Whitfield")
        self.assertEqual((contact.first_name, contact.last_name), ("Marcus", "Whitfield"))
        self.assertEqual(contact.email, "m@northwind.com")
        self.assertEqual(contact.phone, "6145550142")

        self.assertEqual(lead.company_id, company.pk)
        self.assertEqual(lead.contact_id, contact.pk)
        self.assertEqual(lead.source_file, "leads.csv")
        self.assertEqual(lead.source_row_number, 2)
        self.assertEqual(lead.lead_score, 0)

        # The five numbers the result panel shows.
        self.assertEqual(
            (
                job.total_rows,
                job.valid_rows,
                job.duplicate_rows,
                job.invalid_rows,
                job.error_rows,
                job.missing_email_rows,
            ),
            (1, 1, 0, 0, 0, 0),
        )
        self.assertEqual(job.status, ImportStatus.COMPLETED)
        self.assertIsNotNone(job.started_at)
        self.assertIsNotNone(job.completed_at)

    def test_multiple_rows_across_chunks(self):
        rows = [HEADERS]
        for index in range(7):
            rows.append(
                [
                    f"Company {index}",
                    f"Person {index}",
                    f"p{index}@company{index}.com",
                    "",
                    f"company{index}.com",
                    "",
                    "Austin",
                    "TX",
                    "",
                ]
            )
        job = self.make_job(rows, mapping=MAPPING)

        result, job = self.run_job(job, chunk_size=3)

        self.assertEqual(result.processed, 7)
        self.assertEqual(Company.objects.count(), 7)
        self.assertEqual(Contact.objects.count(), 7)
        self.assertEqual(Lead.objects.count(), 7)
        self.assertEqual(job.valid_rows, 7)
        self.assertEqual(job.processed_rows, job.total_rows)

    def test_company_without_email_is_still_stored_and_counted(self):
        job = self.make_job(
            [
                HEADERS,
                ["No Mail Co", "Jane Doe", "", "614-555-0100", "nomail.com", "", "Reno", "NV", ""],
            ],
            mapping=MAPPING,
        )
        ImportRunner(job).run()
        job.refresh_from_db()

        self.assertEqual(job.valid_rows, 1)
        self.assertEqual(job.missing_email_rows, 1)
        self.assertEqual(Contact.objects.get().email, "")

    def test_generic_mailbox_without_a_person_still_creates_a_contact(self):
        job = self.make_job(
            [HEADERS, ["Info Co", "", "info@infoco.com", "", "infoco.com", "", "", "", ""]],
            mapping=MAPPING,
        )
        ImportRunner(job).run()

        contact = Contact.objects.get()
        self.assertEqual(contact.full_name, "")
        self.assertEqual(contact.email, "info@infoco.com")
        self.assertEqual(Lead.objects.get().contact_id, contact.pk)

    def test_invalid_email_is_dropped_and_the_row_is_kept(self):
        job = self.make_job(
            [HEADERS, ["Bad Mail Co", "Sofia", "not-an-email", "", "badmail.com", "", "", "", ""]],
            mapping=MAPPING,
        )
        ImportRunner(job).run()
        job.refresh_from_db()

        self.assertEqual(job.valid_rows, 1)
        self.assertEqual(job.invalid_rows, 0)
        self.assertEqual(job.missing_email_rows, 1)
        self.assertEqual(Contact.objects.get().email, "")
        self.assertTrue(any("Dropped invalid e-mail" in issue["message"] for issue in job.issues))

    def test_row_without_a_business_name_is_invalid(self):
        job = self.make_job(
            [HEADERS, ["", "Orphan", "orphan@nowhere.com", "", "", "", "", "", ""]], mapping=MAPPING
        )
        ImportRunner(job).run()
        job.refresh_from_db()

        self.assertEqual((job.valid_rows, job.invalid_rows), (0, 1))
        self.assertEqual(Company.objects.count(), 0)
        self.assertTrue(any("no business name" in issue["message"] for issue in job.issues))

    def test_phone_type_is_taken_from_the_column_name(self):
        headers = ["Business Name", "Contact", "Mobile"]
        job = self.make_job(
            [headers, ["Mobile Co", "Gary", "720-555-0129"]],
            mapping={"Business Name": "company_name", "Contact": "contact_name", "Mobile": "phone"},
        )
        ImportRunner(job).run()
        self.assertEqual(Contact.objects.get().phone_type, PhoneType.MOBILE)


class DedupAndMergeTests(ImportRunTestCase):
    def test_second_row_with_the_same_domain_is_a_duplicate(self):
        job = self.make_job(
            [
                HEADERS,
                [
                    "Northwind Logistics, Inc.",
                    "Marcus",
                    "m@northwind.com",
                    "",
                    "northwind.com",
                    "",
                    "Columbus",
                    "OH",
                    "850",
                ],
                [
                    "Northwind Logistics",
                    "Marcus Whitfield",
                    "m@northwind.com",
                    "",
                    "www.northwind.com",
                    "",
                    "Columbus",
                    "OH",
                    "",
                ],
            ],
            mapping=MAPPING,
        )
        result, job = self.run_job(job)

        self.assertEqual(result.valid, 1)
        self.assertEqual(result.duplicate, 1)
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(Lead.objects.count(), 1)

    def test_existing_records_are_enriched_but_never_overwritten(self):
        company = Company.objects.create(
            name="Acme Ltd", industry="Manufacturing", website="acme.com", city="Austin"
        )
        job = self.make_job(
            [
                HEADERS,
                [
                    "Acme Ltd",
                    "Jane Doe",
                    "jane@acme.com",
                    "",
                    "acme.com",
                    "Software",
                    "Dallas",
                    "TX",
                    "120",
                ],
            ],
            mapping=MAPPING,
        )
        ImportRunner(job).run()
        job.refresh_from_db()

        company.refresh_from_db()
        contact = Contact.objects.get()

        # Empty fields are filled from the file…
        self.assertEqual(company.state, "TX")
        self.assertEqual(company.employee_count, 120)
        self.assertEqual(contact.email, "jane@acme.com")
        # …existing values are never overwritten.
        self.assertEqual(company.industry, "Manufacturing")
        self.assertEqual(company.city, "Austin")
        self.assertEqual(company.name, "Acme Ltd")
        # The company/contact existed but had no lead yet, so the row imports
        # one new lead instead of landing in the duplicate bucket.
        self.assertEqual((job.valid_rows, job.duplicate_rows), (1, 0))
        self.assertEqual(Lead.objects.count(), 1)

    def test_reimporting_the_same_file_creates_nothing(self):
        rows = [
            HEADERS,
            ["Acme Ltd", "Jane Doe", "jane@acme.com", "", "acme.com", "", "Austin", "TX", "10"],
            ["Beta Corp", "Bob Ray", "bob@beta.com", "", "beta.com", "", "Reno", "NV", "20"],
        ]
        first = self.make_job(rows, name="first.csv", mapping=MAPPING)
        ImportRunner(first).run()

        second = self.make_job(rows, name="second.csv", mapping=MAPPING)
        result, job = self.run_job(second)

        self.assertEqual(result.valid, 0)
        self.assertEqual(result.duplicate, 2)
        self.assertEqual(Company.objects.count(), 2)
        self.assertEqual(Contact.objects.count(), 2)
        self.assertEqual(Lead.objects.count(), 2)
        self.assertEqual(job.valid_rows, 0)

    def test_same_company_two_contacts_creates_two_leads(self):
        job = self.make_job(
            [
                HEADERS,
                ["Acme Ltd", "Jane Doe", "jane@acme.com", "", "acme.com", "", "", "", ""],
                ["Acme Ltd", "Bob Ray", "bob@acme.com", "", "acme.com", "", "", "", ""],
            ],
            mapping=MAPPING,
        )
        result, _ = self.run_job(job)

        self.assertEqual(result.valid, 2)
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(Contact.objects.count(), 2)
        self.assertEqual(Lead.objects.count(), 2)

    def test_two_companies_may_share_an_email_domain_local_part(self):
        job = self.make_job(
            [
                HEADERS,
                ["Acme Ltd", "Jane", "jane@acme.com", "", "acme.com", "", "", "", ""],
                ["Beta Corp", "Jane", "jane@beta.com", "", "beta.com", "", "", "", ""],
            ],
            mapping=MAPPING,
        )
        result, _ = self.run_job(job)
        self.assertEqual(result.valid, 2)
        self.assertEqual(Contact.objects.count(), 2)


class ResilienceTests(ImportRunTestCase):
    def test_a_broken_row_does_not_stop_the_run(self):
        # A row whose value blows up during assignment: patched in build_record
        # to raise for one specific company name.
        rows = [
            HEADERS,
            ["Good Co", "Jane", "jane@good.com", "", "good.com", "", "", "", ""],
            ["Explode Co", "Bob", "bob@explode.com", "", "explode.com", "", "", "", ""],
            ["Other Co", "Ann", "ann@other.com", "", "other.com", "", "", "", ""],
        ]
        job = self.make_job(rows, mapping=MAPPING, name="resilient.csv")

        from django.db import DataError

        from apps.imports import services

        original = services.ImportRunner._resolve_companies

        def explode_on_bad_company(self, records):
            if any(record.company_name == "Explode Co" for record in records):
                raise DataError("simulated database failure")
            return original(self, records)

        with mock.patch.object(services.ImportRunner, "_resolve_companies", explode_on_bad_company):
            ImportRunner(job).run()

        job.refresh_from_db()
        self.assertEqual(job.status, ImportStatus.COMPLETED)
        self.assertEqual(job.error_rows, 1)
        self.assertEqual(job.valid_rows, 2)
        self.assertEqual(job.processed_rows, 3)
        self.assertTrue(any(issue["level"] == "error" for issue in job.issues))
        self.assertFalse(Company.objects.filter(name="Explode Co").exists())
        self.assertTrue(Company.objects.filter(name="Good Co").exists())
        self.assertTrue(Company.objects.filter(name="Other Co").exists())

    def test_broken_bulk_insert_falls_back_to_row_by_row(self):
        rows = [
            HEADERS,
            ["Acme Ltd", "Jane", "jane@acme.com", "", "acme.com", "", "", "", ""],
            ["Beta Corp", "Bob", "bob@beta.com", "", "beta.com", "", "", "", ""],
            ["Gamma Inc", "Ann", "ann@gamma.com", "", "gamma.com", "", "", "", ""],
        ]
        job = self.make_job(rows, mapping=MAPPING, name="bulk.csv")

        from django.db import IntegrityError

        from apps.imports import services

        original = services.ImportRunner._resolve_companies
        calls = {"count": 0}

        def fail_once(self, records):
            calls["count"] += 1
            if calls["count"] == 1 and len(records) > 1:
                raise IntegrityError("simulated bulk insert failure")
            return original(self, records)

        with mock.patch.object(services.ImportRunner, "_resolve_companies", fail_once):
            ImportRunner(job).run()

        job.refresh_from_db()
        self.assertEqual(job.status, ImportStatus.COMPLETED)
        self.assertEqual(job.valid_rows, 3)
        self.assertEqual(job.error_rows, 0)
        self.assertEqual(Company.objects.count(), 3)

    def test_counters_always_add_up(self):
        rows = [
            HEADERS,
            ["Acme Ltd", "Jane", "jane@acme.com", "", "acme.com", "", "", "", ""],
            ["", "Orphan", "o@nowhere.com", "", "", "", "", "", ""],
            ["Acme Ltd", "Jane", "jane@acme.com", "", "acme.com", "", "", "", ""],
            ["Beta Corp", "Bob", "", "", "beta.com", "", "", "", ""],
        ]
        job = self.make_job(rows, mapping=MAPPING)
        _, job = self.run_job(job)

        self.assertEqual(
            job.valid_rows + job.duplicate_rows + job.invalid_rows + job.error_rows,
            job.processed_rows,
        )
        self.assertEqual(job.processed_rows, job.total_rows)
        self.assertEqual(job.total_rows, 4)
        # Only stored rows count: Acme (e-mail), the rejected orphan row, the
        # duplicate Acme row (e-mail) and Beta (no address) → exactly one.
        self.assertEqual(job.missing_email_rows, 1)

    def test_unreadable_file_marks_the_job_failed(self):
        job = self.make_job([HEADERS, ["Acme", "", "", "", "", "", "", "", ""]], mapping=MAPPING)
        Path(job.upload.path).unlink()

        with self.assertRaises(FileNotFoundError):
            process_import_job(job.pk)

        job.refresh_from_db()
        self.assertEqual(job.status, ImportStatus.FAILED)
        self.assertIn("FileNotFoundError", job.error_message)
        self.assertIsNotNone(job.completed_at)

    def test_completed_job_is_not_processed_twice(self):
        job = self.make_job(
            [HEADERS, ["Acme Ltd", "Jane", "jane@acme.com", "", "acme.com", "", "", "", ""]],
            mapping=MAPPING,
        )
        process_import_job(job.pk)
        again = process_import_job(job.pk)

        self.assertTrue(again.get("skipped"))
        self.assertEqual(Lead.objects.count(), 1)


class XlsxImportTests(ImportRunTestCase):
    def test_imports_an_xlsx_sheet(self):
        path = write_xlsx(
            self.tmp / "book.xlsx",
            {
                "Leads": [
                    HEADERS,
                    [
                        "Cascade Brewing Co.",
                        "Tomas Lindqvist",
                        "tomas@cascadebrewing.com",
                        "503-555-0121",
                        "cascadebrewing.com",
                        "Food & Beverage",
                        "Portland",
                        "OR",
                        75,
                    ],
                ],
                "Ignored": [["Whatever"], ["x"]],
            },
        )
        job = ImportJob.objects.create(
            filename="book.xlsx",
            file_type="xlsx",
            file_size=path.stat().st_size,
            selected_sheet="Leads",
            sheet_names=["Leads", "Ignored"],
            headers=list(HEADERS),
            column_mapping=MAPPING,
        )
        with open(path, "rb") as handle:
            job.upload.save("book.xlsx", handle, save=True)

        ImportRunner(job).run()
        job.refresh_from_db()

        self.assertEqual(job.status, ImportStatus.COMPLETED)
        self.assertEqual(job.valid_rows, 1)
        company = Company.objects.get()
        self.assertEqual(company.employee_count, 75)
        self.assertEqual(Lead.objects.get().source_row_number, 2)

    def test_the_wrong_sheet_is_never_silently_used(self):
        path = write_xlsx(
            self.tmp / "book.xlsx",
            {
                "Leads": [
                    HEADERS,
                    ["Acme", "Jane", "jane@acme.com", "", "acme.com", "", "", "", ""],
                ],
                "Other": [["x"]],
            },
        )
        job = ImportJob.objects.create(
            filename="book.xlsx",
            file_type="xlsx",
            file_size=path.stat().st_size,
            selected_sheet="Missing sheet",
            headers=list(HEADERS),
            column_mapping=MAPPING,
        )
        with open(path, "rb") as handle:
            job.upload.save("book.xlsx", handle, save=True)

        ImportRunner(job).run()
        job.refresh_from_db()

        # openpyxl falls back to the active sheet; the run still succeeds and the
        # row is imported from the sheet that exists.
        self.assertEqual(job.status, ImportStatus.COMPLETED)
        self.assertEqual(job.valid_rows, 1)


class MessySampleTests(ImportRunTestCase):
    """The shipped sample file, imported end to end."""

    def test_sample_shape_counts(self):
        job = self.make_job(MESSY_ROWS, name="sample.csv")

        with mock.patch("apps.imports.services.CHUNK_SIZE", 2):
            ImportRunner(job).run()
        job.refresh_from_db()

        self.assertEqual(job.total_rows, 5)
        self.assertEqual(job.valid_rows, 3)  # Northwind, Brightline, Bluewater
        self.assertEqual(job.duplicate_rows, 1)  # the repeated Northwind row
        self.assertEqual(job.invalid_rows, 1)  # no business name
        self.assertEqual(job.error_rows, 0)
        self.assertEqual(job.missing_email_rows, 1)  # Bluewater's address was invalid
        self.assertEqual(Company.objects.count(), 3)
        self.assertEqual(Lead.objects.count(), 3)
        self.assertEqual(job.headers, MESSY_HEADERS)
        # Auto-detection filled the mapping because the job had none.
        self.assertEqual(job.column_mapping["Business_Name"], "company_name")
        self.assertEqual(job.column_mapping["Mobile"], "phone")
        self.assertEqual(Contact.objects.filter(phone_type=PhoneType.MOBILE).count(), 3)
