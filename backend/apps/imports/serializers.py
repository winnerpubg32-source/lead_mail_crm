"""Serializers for the Imports API."""

from __future__ import annotations

from rest_framework import serializers

from apps.imports.mapping import system_fields_payload
from apps.imports.models import ImportJob

__all__ = [
    "ImportJobDetailSerializer",
    "ImportJobSerializer",
    "StartImportSerializer",
    "UploadSerializer",
]


class ImportJobSerializer(serializers.ModelSerializer):
    """
    Import history / progress row.

    Shapes the counters into the three blocks the UI needs: the file card, the
    progress bar and the "Import completed" result panel.
    """

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    uploaded = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    class Meta:
        model = ImportJob
        fields = (
            "id",
            "filename",
            "status",
            "status_display",
            "file_type",
            "file_size",
            "uploaded",
            "progress",
            "summary",
            "total_rows",
            "processed_rows",
            "valid_rows",
            "invalid_rows",
            "duplicate_rows",
            "error_rows",
            "missing_email_rows",
            "new_companies",
            "new_contacts",
            "started_at",
            "completed_at",
            "duration_seconds",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_uploaded(self, obj: ImportJob) -> dict:
        return {
            "file_type": obj.file_type,
            "file_size": obj.file_size,
            "sheets": list(obj.sheet_names or []),
            "sheet_count": len(obj.sheet_names or []),
            "selected_sheet": obj.selected_sheet,
            "encoding": obj.encoding,
            "delimiter": obj.delimiter,
            "row_count": obj.total_rows,
        }

    def get_progress(self, obj: ImportJob) -> dict:
        return {
            "processed": obj.processed_rows,
            "total": obj.total_rows,
            "percent": obj.progress_percent,
            "is_active": obj.is_active,
            "awaiting_review": obj.is_awaiting_review,
        }

    def get_summary(self, obj: ImportJob) -> dict:
        """The five numbers of the result panel, in the brief's wording."""
        return {
            "Total": obj.total_rows,
            "Imported": obj.valid_rows,
            "Duplicates": obj.duplicate_rows,
            "Invalid": obj.invalid_rows,
            "Missing Email": obj.missing_email_rows,
            "Errors": obj.error_rows,
            "New companies": obj.new_companies,
            "New contacts": obj.new_contacts,
        }


class ImportJobDetailSerializer(ImportJobSerializer):
    """Adds the preview payload and the row-level issue sample."""

    preview = serializers.SerializerMethodField()

    class Meta(ImportJobSerializer.Meta):
        fields = (
            *ImportJobSerializer.Meta.fields,
            "preview",
            "issues",
            "error_message",
            "headers",
            "column_mapping",
        )
        read_only_fields = fields

    def get_preview(self, obj: ImportJob) -> dict:
        analysis = obj.analysis or {}
        return {
            "columns": analysis.get("columns", []),
            "mapping": analysis.get("mapping", obj.column_mapping or {}),
            "sample_rows": analysis.get("sample_rows", []),
            "system_fields": system_fields_payload(),
            "counts": {
                "total_rows": analysis.get("total_rows", obj.total_rows),
                "rows_with_email": analysis.get("rows_with_email", 0),
                "rows_without_email": analysis.get("rows_without_email", 0),
                "potential_duplicates": analysis.get("potential_duplicates", 0),
                "invalid_emails": analysis.get("invalid_emails", 0),
            },
            "issues": analysis.get("issues", []),
        }


class UploadSerializer(serializers.Serializer):
    """``POST /api/v1/imports/upload/`` — the multipart upload itself."""

    file = serializers.FileField()
    sheet = serializers.CharField(required=False, allow_blank=True)

    def validate_file(self, value):
        from apps.imports.parsers import UnsupportedFileType, detect_file_type

        max_bytes = 100 * 1024 * 1024
        if value.size > max_bytes:
            raise serializers.ValidationError("Files larger than 100 MB are not supported.")
        try:
            # Trust content, not just the extension: renamed files still work
            # and unsupported ones are rejected before anything is stored.
            detect_file_type(value.name)
        except (UnsupportedFileType, OSError) as exc:
            raise serializers.ValidationError(
                "Unsupported file type. Upload a .csv, .xlsx or .xlsm file."
            ) from exc
        return value


class StartImportSerializer(serializers.Serializer):
    """``POST /api/v1/imports/{id}/start/`` — confirm mapping and run."""

    column_mapping = serializers.DictField(
        child=serializers.CharField(allow_null=True, allow_blank=True), required=False
    )
    sheet = serializers.CharField(required=False, allow_blank=True)

    def validate_column_mapping(self, value):
        from apps.imports.mapping import FIELD_BY_KEY

        unknown = sorted(
            {target for target in value.values() if target and target not in FIELD_BY_KEY}
        )
        if unknown:
            raise serializers.ValidationError(f"Unknown system field(s): {', '.join(unknown)}")
        return value
