"""Admin registration for the Imports module."""

from __future__ import annotations

from django.contrib import admin

from apps.imports.models import ImportJob


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    """Read-mostly admin: the counters are written by the import runner."""

    list_display = (
        "id",
        "filename",
        "status",
        "total_rows",
        "valid_rows",
        "duplicate_rows",
        "invalid_rows",
        "error_rows",
        "created_at",
    )
    list_filter = ("status", "file_type")
    search_fields = ("filename", "error_message")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    readonly_fields = (
        "analysis",
        "issues",
        "started_at",
        "completed_at",
        "processed_rows",
        "valid_rows",
        "invalid_rows",
        "duplicate_rows",
        "error_rows",
        "missing_email_rows",
        "new_companies",
        "new_contacts",
    )
