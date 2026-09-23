"""
Background-processing tests: the Celery task and the no-broker fallback.

The sandbox and CI have no worker running, so these tests never wait for real
asynchronous work: the dispatch decision is what matters here, while the run
itself is covered by ``test_services``.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import mock

from django.test import TestCase

from apps.imports.models import ImportJob, ImportStatus
from apps.imports.services import enqueue_import_job, process_import_job
from apps.imports.tasks import run_import_job
from apps.imports.tests.factories import MESSY_ROWS, write_csv


class CeleryWiringTests(TestCase):
    def test_the_task_is_registered_under_a_stable_name(self):
        self.assertEqual(run_import_job.name, "imports.run_import_job")
        self.assertIn("imports.run_import_job", run_import_job.app.tasks)

    def test_the_task_carries_only_a_job_id(self):
        signature = run_import_job.s(42)
        self.assertEqual(signature.args, (42,))
        self.assertEqual(signature.kwargs, {})

    def test_the_task_is_retried_and_acknowledged_late(self):
        self.assertEqual(run_import_job.max_retries, 2)
        self.assertTrue(run_import_job.acks_late)


class EnqueueTests(TestCase):
    def setUp(self):
        super().setUp()
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        path = write_csv(self.tmp / "leads.csv", MESSY_ROWS)
        job = ImportJob.objects.create(
            filename="leads.csv", file_type="csv", file_size=path.stat().st_size
        )
        with open(path, "rb") as handle:
            job.upload.save("leads.csv", handle, save=True)
        self.job = job

    def test_broker_available_dispatches_to_celery(self):
        with mock.patch("apps.imports.tasks.run_import_job.delay") as delay:
            mode = enqueue_import_job(self.job)

        self.assertEqual(mode, "celery")
        delay.assert_called_once_with(self.job.pk)

    def test_broker_errors_fall_back_to_a_background_thread(self):
        with (
            mock.patch(
                "apps.imports.tasks.run_import_job.delay", side_effect=OSError("broker down")
            ),
            mock.patch("threading.Thread") as thread,
        ):
            mode = enqueue_import_job(self.job)

        self.assertEqual(mode, "thread")
        thread.assert_called_once()
        self.assertEqual(thread.return_value.start.call_count, 1)

    def test_running_job_is_skipped_when_processed_twice(self):
        ImportJob.objects.filter(pk=self.job.pk).update(status=ImportStatus.PROCESSING)
        outcome = process_import_job(self.job.pk)

        self.assertTrue(outcome["skipped"])
        self.assertEqual(outcome["status"], ImportStatus.PROCESSING)

    def test_process_import_job_returns_a_broker_safe_summary(self):
        outcome = process_import_job(self.job.pk)

        self.assertEqual(outcome["job"], self.job.pk)
        self.assertEqual(outcome["status"], ImportStatus.COMPLETED)
        self.assertEqual(outcome["processed"], 5)
        self.assertEqual(outcome["imported"], 3)
        self.assertEqual(outcome["duplicates"], 1)
        self.assertEqual(outcome["invalid"], 1)
        self.assertEqual(outcome["missing_email"], 1)
        # Everything in it must be JSON serialisable for the result backend.
        import json

        json.dumps(outcome)
