"""
Celery tasks for the Imports module.

``run_import_job`` is deliberately thin: the work lives in
:mod:`apps.imports.services` so it can also be driven from a management command,
a test or the thread fallback used when no broker is reachable.
"""

from __future__ import annotations

from celery import shared_task

from apps.imports.services import process_import_job

__all__ = ["run_import_job"]


@shared_task(
    name="imports.run_import_job",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def run_import_job(self, job_id: int) -> dict:
    """
    Process one uploaded file.

    The task carries only the job id — the file is re-read from storage inside
    the worker, so the message stays small no matter how big the upload is.
    """
    return process_import_job(job_id)
