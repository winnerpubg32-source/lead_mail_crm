"""
Import models.

An ``ImportJob`` is one uploaded file moving through the import pipeline:

``upload`` → *QUEUED* (stored, analysed, waiting for the user to confirm the
column mapping) → *PROCESSING* (Celery worker writes rows in chunks)
→ *COMPLETED* or *FAILED*.

The counters are updated after every chunk, so the progress endpoint can poll a
single row without touching the file again. The uploaded file itself is kept in
``MEDIA_ROOT/imports/`` for the lifetime of the job: the worker re-reads it
instead of holding megabytes of rows in memory or in the broker.
"""

from __future__ import annotations

import os

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel

__all__ = ["ImportJob", "ImportStatus", "upload_path"]


class ImportStatus(models.TextChoices):
    """Lifecycle of an import run."""

    QUEUED = "QUEUED", _("Queued")
    PROCESSING = "PROCESSING", _("Processing")
    COMPLETED = "COMPLETED", _("Completed")
    FAILED = "FAILED", _("Failed")


#: Statuses that mean the job is still going to change.
ACTIVE_STATUSES = frozenset({ImportStatus.QUEUED, ImportStatus.PROCESSING})


def upload_path(instance: ImportJob, filename: str) -> str:
    """``imports/<id>/<original name>`` — one folder per job, original name kept."""
    safe_name = os.path.basename(filename).replace(os.sep, "_") or "upload"
    return f"imports/{instance.pk or 'new'}/{safe_name}"


class ImportJob(TimeStampedModel):
    """
    One CSV/XLSX upload and its progress.

    The fields listed in the product brief (``filename``, ``status``,
    ``total_rows``, ``processed_rows``, ``valid_rows``, ``invalid_rows``,
    ``duplicate_rows``, ``error_rows``, ``started_at``, ``completed_at``) are the
    contract the UI reads. The remaining fields are supporting state:
    the stored file, what the parser detected (``sheet_names``, ``headers``,
    ``file_type``, ``file_size``), the user-confirmed ``column_mapping``, the
    cached ``analysis`` used by the preview, ``missing_email_rows`` for the
    result panel, and ``issues`` (a bounded sample of row-level problems).
    """

    MAX_ISSUES = 50

    filename = models.CharField(_("filename"), max_length=255)
    status = models.CharField(
        _("status"),
        max_length=16,
        choices=ImportStatus.choices,
        default=ImportStatus.QUEUED,
        db_index=True,
    )

    # --- File -----------------------------------------------------------------
    upload = models.FileField(_("file"), upload_to=upload_path, blank=True)
    file_type = models.CharField(_("file type"), max_length=8, blank=True)  # csv | xlsx
    file_size = models.PositiveBigIntegerField(_("file size"), default=0)
    encoding = models.CharField(_("encoding"), max_length=32, blank=True)
    delimiter = models.CharField(_("delimiter"), max_length=4, blank=True)
    sheet_names = models.JSONField(_("sheets"), default=list, blank=True)
    selected_sheet = models.CharField(_("selected sheet"), max_length=255, blank=True)
    headers = models.JSONField(_("source columns"), default=list, blank=True)

    # --- Mapping --------------------------------------------------------------
    #: ``{"Business Name": "company_name", "Corporate Email": "email", …}``
    column_mapping = models.JSONField(_("column mapping"), default=dict, blank=True)
    #: Cached preview: counts, first 50 rows, per-column detection details.
    analysis = models.JSONField(_("analysis"), default=dict, blank=True)

    # --- Progress -------------------------------------------------------------
    total_rows = models.PositiveIntegerField(_("total rows"), default=0)
    processed_rows = models.PositiveIntegerField(_("processed rows"), default=0)
    valid_rows = models.PositiveIntegerField(_("valid rows"), default=0)
    invalid_rows = models.PositiveIntegerField(_("invalid rows"), default=0)
    duplicate_rows = models.PositiveIntegerField(_("duplicate rows"), default=0)
    error_rows = models.PositiveIntegerField(_("error rows"), default=0)
    missing_email_rows = models.PositiveIntegerField(_("rows without e-mail"), default=0)
    new_companies = models.PositiveIntegerField(_("new companies"), default=0)
    new_contacts = models.PositiveIntegerField(_("new contacts"), default=0)

    #: Bounded sample of row problems: ``[{"row": 12, "level": "invalid", …}]``
    issues = models.JSONField(_("issues"), default=list, blank=True)
    error_message = models.TextField(_("error message"), blank=True)

    started_at = models.DateTimeField(_("started at"), null=True, blank=True)
    completed_at = models.DateTimeField(_("completed at"), null=True, blank=True)

    class Meta:
        verbose_name = _("import job")
        verbose_name_plural = _("import jobs")
        ordering = ("-created_at", "-id")
        indexes = (
            models.Index(fields=["status", "-created_at"], name="import_status_created_idx"),
            models.Index(fields=["filename"], name="import_filename_idx"),
        )

    def __str__(self) -> str:
        return f"{self.filename} ({self.status})"

    # --- Derived state --------------------------------------------------------
    @property
    def is_active(self) -> bool:
        return self.status in ACTIVE_STATUSES

    @property
    def is_awaiting_review(self) -> bool:
        """Uploaded and analysed, but the import has not been started yet."""
        return self.status == ImportStatus.QUEUED and self.started_at is None

    @property
    def progress_percent(self) -> int:
        if not self.total_rows:
            return 100 if self.status == ImportStatus.COMPLETED else 0
        return min(100, round(self.processed_rows * 100 / self.total_rows))

    @property
    def duration_seconds(self) -> float | None:
        if not self.started_at:
            return None
        end = self.completed_at or self.updated_at
        return round((end - self.started_at).total_seconds(), 2)

    def record_issue(self, row_number: int, level: str, message: str, *, column: str = "") -> None:
        """Keep a bounded sample of row problems (counters stay authoritative)."""
        if len(self.issues) >= self.MAX_ISSUES:
            return
        self.issues = [
            *self.issues,
            {"row": row_number, "level": level, "message": message, "column": column},
        ]
