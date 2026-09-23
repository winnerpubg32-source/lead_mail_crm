"""
API tests for ``/api/v1/imports/`` — upload, preview, mapping, start, history.

The Celery dispatch is patched here: the run itself is covered by
``test_services``; these tests are about the HTTP contract.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.companies.models import Company
from apps.imports.models import ImportJob, ImportStatus
from apps.imports.tests.factories import MESSY_HEADERS, MESSY_ROWS, csv_upload, xlsx_upload
from apps.leads.models import Lead

LIST_URL = "/api/v1/imports/"
UPLOAD_URL = "/api/v1/imports/upload/"


class ImportApiTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.media = tempfile.mkdtemp()

    def setUp(self):
        super().setUp()
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.client = APIClient()

    # --- helpers --------------------------------------------------------------
    def upload(self, rows: list[list[str]] | None = None, name: str = "leads.csv", **kwargs):
        payload = {"file": csv_upload(MESSY_ROWS if rows is None else rows, name, **kwargs)}
        response = self.client.post(UPLOAD_URL, payload, format="multipart")
        return response

    def start(self, job_id: int, body: dict | None = None, dispatch: str = "celery"):
        with mock.patch("apps.imports.views.enqueue_import_job", return_value=dispatch):
            return self.client.post(f"/api/v1/imports/{job_id}/start/", body or {}, format="json")


class UploadTests(ImportApiTestCase):
    def test_csv_upload_is_analysed_and_returns_the_preview(self):
        response = self.upload()
        self.assertEqual(response.status_code, 201, response.data)

        body = response.data
        self.assertEqual(body["status"], ImportStatus.QUEUED)
        self.assertTrue(body["progress"]["awaiting_review"])
        self.assertEqual(body["filename"], "leads.csv")
        self.assertEqual(body["uploaded"]["file_type"], "csv")
        self.assertGreater(body["uploaded"]["file_size"], 0)
        self.assertEqual(body["total_rows"], 5)

        counts = body["preview"]["counts"]
        # Four rows carry a usable address; the fifth (Bluewater) has one that
        # fails syntax validation, so it is reported as "without e-mail" too.
        self.assertEqual(counts["total_rows"], 5)
        self.assertEqual(counts["rows_with_email"], 4)
        self.assertEqual(counts["rows_without_email"], 1)
        self.assertEqual(
            counts["rows_with_email"] + counts["rows_without_email"], counts["total_rows"]
        )
        self.assertEqual(counts["invalid_emails"], 1)
        self.assertEqual(counts["potential_duplicates"], 1)

        self.assertEqual(body["headers"], MESSY_HEADERS)
        self.assertEqual(body["column_mapping"]["Business_Name"], "company_name")
        self.assertEqual(len(body["preview"]["system_fields"]), 20)

    def test_sample_rows_are_capped_at_fifty(self):
        rows = [["Business Name", "E-mail"]]
        rows.extend([f"Company {index}", f"p{index}@example.com"] for index in range(120))

        response = self.upload(rows)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["total_rows"], 120)
        self.assertEqual(len(response.data["preview"]["sample_rows"]), 50)

    def test_xlsx_upload_reports_sheets_and_selects_the_first(self):
        payload = {
            "file": xlsx_upload(
                {
                    "Leads": [MESSY_HEADERS, MESSY_ROWS[1]],
                    "Lookups": [["Industry"], ["Healthcare"]],
                }
            )
        }
        response = self.client.post(UPLOAD_URL, payload, format="multipart")
        self.assertEqual(response.status_code, 201, response.data)

        body = response.data
        self.assertEqual(body["uploaded"]["file_type"], "xlsx")
        self.assertEqual(body["uploaded"]["sheets"], ["Leads", "Lookups"])
        self.assertEqual(body["uploaded"]["sheet_count"], 2)
        self.assertEqual(body["uploaded"]["selected_sheet"], "Leads")
        self.assertEqual(body["total_rows"], 1)

    def test_sheet_can_be_chosen_at_upload_time(self):
        payload = {
            "file": xlsx_upload(
                {"Leads": [MESSY_HEADERS, MESSY_ROWS[1]], "Lookups": [["Industry"], ["Healthcare"]]}
            ),
            "sheet": "Lookups",
        }
        response = self.client.post(UPLOAD_URL, payload, format="multipart")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["uploaded"]["selected_sheet"], "Lookups")
        self.assertEqual(response.data["headers"], ["Industry"])

    def test_unsupported_files_are_rejected(self):
        bogus = SimpleUploadedFile("notes.pdf", b"%PDF-1.4 nope", content_type="application/pdf")
        response = self.client.post(UPLOAD_URL, {"file": bogus}, format="multipart")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "invalid")
        self.assertIn("Unsupported file type", str(response.data["error"]["details"]))
        self.assertEqual(ImportJob.objects.count(), 0)

    def test_oversized_files_are_rejected_by_the_serializer(self):
        # A real multipart round-trip rebuilds the file object, so the size rule
        # is asserted where it lives: on the serializer.
        from apps.imports.serializers import UploadSerializer

        big = SimpleUploadedFile("huge.csv", b"a,b\n", content_type="text/csv")
        big.size = 200 * 1024 * 1024

        serializer = UploadSerializer(data={"file": big})
        self.assertFalse(serializer.is_valid())
        self.assertIn("100 MB", str(serializer.errors["file"]))

    def test_file_without_rows_is_rejected_and_leaves_nothing_behind(self):
        response = self.upload([], name="empty.csv")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "invalid_file")
        self.assertEqual(ImportJob.objects.count(), 0)

    def test_upload_requires_a_file(self):
        response = self.client.post(UPLOAD_URL, {}, format="multipart")
        self.assertEqual(response.status_code, 400)


class MappingTests(ImportApiTestCase):
    def test_mapping_endpoint_applies_manual_changes(self):
        job_id = self.upload(
            [["Contact Person", "Work Email", "Town"], ["Jane", "jane@acme.com", "Austin"]]
        ).data["id"]

        response = self.client.post(
            f"/api/v1/imports/{job_id}/mapping/",
            {
                "column_mapping": {
                    "Contact Person": "company_name",
                    "Work Email": "email",
                    "Town": "city",
                }
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["column_mapping"]["Contact Person"], "company_name")
        job = ImportJob.objects.get(pk=job_id)
        self.assertEqual(job.column_mapping["Contact Person"], "company_name")

    def test_unknown_system_field_is_rejected(self):
        job_id = self.upload().data["id"]
        response = self.client.post(
            f"/api/v1/imports/{job_id}/mapping/",
            {"column_mapping": {"Business_Name": "favourite_colour"}},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_fields_catalog_is_public(self):
        response = self.client.get("/api/v1/imports/fields/")
        self.assertEqual(response.status_code, 200)
        keys = [entry["key"] for entry in response.data["system_fields"]]
        self.assertIn("company_name", keys)
        self.assertIn("email", keys)


class StartTests(ImportApiTestCase):
    def test_start_hands_the_job_to_the_worker(self):
        job_id = self.upload().data["id"]
        response = self.start(job_id)

        self.assertEqual(response.status_code, 202, response.data)
        self.assertEqual(response.data["status"], ImportStatus.QUEUED)
        self.assertEqual(response.data["dispatch"], "celery")

    def test_start_is_rejected_without_a_business_name_column(self):
        job_id = self.upload([["Contact Person", "Work Email"], ["Jane", "jane@acme.com"]]).data[
            "id"
        ]
        response = self.start(job_id)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Business name", response.data["error"]["message"])

    def test_start_accepts_a_mapping_in_the_body(self):
        job_id = self.upload([["Contact Person", "Work Email"], ["Jane", "jane@acme.com"]]).data[
            "id"
        ]
        response = self.start(
            job_id, {"column_mapping": {"Contact Person": "company_name", "Work Email": "email"}}
        )

        self.assertEqual(response.status_code, 202)
        job = ImportJob.objects.get(pk=job_id)
        self.assertEqual(job.column_mapping["Contact Person"], "company_name")

    def test_completed_job_cannot_be_started_again(self):
        job_id = self.upload().data["id"]
        ImportJob.objects.filter(pk=job_id).update(status=ImportStatus.COMPLETED)

        response = self.start(job_id)
        self.assertEqual(response.status_code, 409)

    def test_running_job_reports_conflict(self):
        job_id = self.upload().data["id"]
        ImportJob.objects.filter(pk=job_id).update(status=ImportStatus.PROCESSING)

        response = self.start(job_id)
        self.assertEqual(response.status_code, 409)


class ProgressAndDetailTests(ImportApiTestCase):
    def test_status_endpoint_returns_progress(self):
        job_id = self.upload().data["id"]
        ImportJob.objects.filter(pk=job_id).update(
            status=ImportStatus.PROCESSING,
            total_rows=100,
            processed_rows=25,
            valid_rows=20,
            duplicate_rows=3,
            invalid_rows=2,
        )

        response = self.client.get(f"/api/v1/imports/{job_id}/status/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["progress"]["percent"], 25)
        self.assertTrue(response.data["progress"]["is_active"])

    def test_detail_carries_the_preview_and_issues(self):
        job_id = self.upload().data["id"]
        ImportJob.objects.filter(pk=job_id).update(
            issues=[{"row": 12, "level": "warning", "message": "Dropped invalid e-mail address"}]
        )

        response = self.client.get(f"/api/v1/imports/{job_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["preview"]["counts"]["total_rows"], 5)
        self.assertEqual(response.data["issues"][0]["row"], 12)
        self.assertEqual(response.data["summary"]["Total"], 5)

    def test_preview_endpoint_returns_the_payload_directly(self):
        job_id = self.upload().data["id"]
        response = self.client.get(f"/api/v1/imports/{job_id}/preview/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("sample_rows", response.data)
        self.assertIn("system_fields", response.data)

    def test_unknown_job_is_a_404(self):
        self.assertEqual(self.client.get("/api/v1/imports/999999/").status_code, 404)


class DiscardTests(ImportApiTestCase):
    def test_cancel_deletes_the_job_and_its_file(self):
        job = ImportJob.objects.get(pk=self.upload().data["id"])
        stored = Path(job.upload.path)
        self.assertTrue(stored.exists())

        response = self.client.post(f"/api/v1/imports/{job.pk}/cancel/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ImportJob.objects.filter(pk=job.pk).exists())
        self.assertFalse(stored.exists())

    def test_delete_behaves_like_cancel(self):
        job_id = self.upload().data["id"]
        response = self.client.delete(f"/api/v1/imports/{job_id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ImportJob.objects.filter(pk=job_id).exists())

    def test_a_running_job_cannot_be_discarded(self):
        job_id = self.upload().data["id"]
        ImportJob.objects.filter(pk=job_id).update(status=ImportStatus.PROCESSING)

        response = self.client.post(f"/api/v1/imports/{job_id}/cancel/")
        self.assertEqual(response.status_code, 409)
        self.assertTrue(ImportJob.objects.filter(pk=job_id).exists())


class HistoryTests(ImportApiTestCase):
    def setUp(self):
        super().setUp()
        self.first = ImportJob.objects.create(
            filename="january.csv",
            file_type="csv",
            status=ImportStatus.COMPLETED,
            total_rows=100,
            valid_rows=90,
            duplicate_rows=8,
            invalid_rows=2,
            missing_email_rows=5,
        )
        self.second = ImportJob.objects.create(
            filename="february.xlsx",
            file_type="xlsx",
            status=ImportStatus.FAILED,
            total_rows=10,
            error_rows=4,
        )
        self.third = ImportJob.objects.create(
            filename="march.csv", file_type="csv", status=ImportStatus.QUEUED
        )

    def test_history_is_paginated_and_newest_first(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(response.data["results"][0]["filename"], "march.csv")
        self.assertEqual(
            set(response.data["results"][0]["summary"]),
            {
                "Total",
                "Imported",
                "Duplicates",
                "Invalid",
                "Missing Email",
                "Errors",
                "New companies",
                "New contacts",
            },
        )

    def test_filter_by_status_and_file_type(self):
        completed = self.client.get(f"{LIST_URL}?status=COMPLETED").data
        self.assertEqual(completed["count"], 1)
        self.assertEqual(completed["results"][0]["filename"], "january.csv")

        xlsx = self.client.get(f"{LIST_URL}?file_type=xlsx").data
        self.assertEqual(xlsx["count"], 1)

    def test_filter_with_errors(self):
        with_errors = self.client.get(f"{LIST_URL}?with_errors=true").data
        self.assertEqual(with_errors["count"], 1)
        self.assertEqual(with_errors["results"][0]["filename"], "february.xlsx")

    def test_search_and_ordering(self):
        self.assertEqual(self.client.get(f"{LIST_URL}?search=january").data["count"], 1)
        ordered = self.client.get(f"{LIST_URL}?ordering=filename").data["results"]
        self.assertEqual(
            [row["filename"] for row in ordered], ["february.xlsx", "january.csv", "march.csv"]
        )

    def test_module_status_endpoint(self):
        response = self.client.get("/api/v1/imports/status/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "implemented")
        self.assertEqual(response.data["supported_files"], ["csv", "xlsx"])
        self.assertEqual(response.data["jobs"], 3)

    def test_unversioned_alias_serves_the_same_history(self):
        versioned = self.client.get(LIST_URL).data
        unversioned = self.client.get("/api/imports/").data
        self.assertEqual(versioned["count"], unversioned["count"])


class EndToEndApiTests(ImportApiTestCase):
    """Upload → start (run straight away) → poll → result, through the API."""

    def test_upload_start_and_collect_the_result(self):
        job_id = self.upload().data["id"]

        # The worker is simulated by running the service in-process.
        from apps.imports.services import process_import_job

        process_import_job(job_id)

        detail = self.client.get(f"/api/v1/imports/{job_id}/").data
        self.assertEqual(detail["status"], ImportStatus.COMPLETED)
        self.assertEqual(detail["progress"]["percent"], 100)
        self.assertEqual(
            detail["summary"],
            {
                "Total": 5,
                "Imported": 3,
                "Duplicates": 1,
                "Invalid": 1,
                "Missing Email": 1,
                "Errors": 0,
                "New companies": 3,
                "New contacts": 3,
            },
        )
        self.assertEqual(Company.objects.count(), 3)
        self.assertEqual(Lead.objects.count(), 3)
        self.assertEqual(Lead.objects.first().source_file, "leads.csv")
