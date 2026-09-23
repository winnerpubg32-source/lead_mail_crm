"""
Imports API.

Endpoints (all under ``/api/v1/imports/``; every route is also served from the
unversioned ``/api/imports/`` alias):

===========================  =================================================
``GET    /imports/``         Import history — paginated, filterable
``GET    /imports/fields/``  System-field catalog for the mapping dropdowns
``GET    /imports/status/``  Module status + totals
``POST   /imports/upload/``  Upload a CSV/XLSX; returns the analysed job
``GET    /imports/{id}/``    One job: counters, preview payload, issues
``GET    /imports/{id}/preview/``   Preview only (counts, columns, first 50 rows)
``POST   /imports/{id}/mapping/``   Re-detect / validate a column mapping
``POST   /imports/{id}/start/``     Confirm and start the (Celery) import
``GET    /imports/{id}/status/``    Light progress payload for polling
``POST   /imports/{id}/cancel/``    Discard an upload (deletes the job + file)
``DELETE /imports/{id}/``           Same as cancel
===========================  =================================================

Upload is synchronous only up to the *analysis* (one streaming pass: counts,
detected columns, first 50 rows). The import run itself always goes to Celery —
see :func:`apps.imports.services.enqueue_import_job`.
"""

from __future__ import annotations

from django.db.models import Sum
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.imports.analysis import analyze_file, describe_file
from apps.imports.filters import ImportJobFilter
from apps.imports.mapping import detect_mapping, system_fields_payload
from apps.imports.models import ImportJob, ImportStatus
from apps.imports.parsers import UnsupportedFileType, detect_file_type, header_row
from apps.imports.records import MappingError, build_plan
from apps.imports.serializers import (
    ImportJobDetailSerializer,
    ImportJobSerializer,
    StartImportSerializer,
    UploadSerializer,
)
from apps.imports.services import enqueue_import_job
from core.filters import NullsLastOrderingFilter


class ImportJobViewSet(ModelViewSet):
    """CRUD-ish viewset: upload, preview, start, poll, discard, history."""

    queryset = ImportJob.objects.all()
    serializer_class = ImportJobSerializer
    filterset_class = ImportJobFilter
    search_fields = ("filename",)
    ordering_fields = (
        "created_at",
        "filename",
        "total_rows",
        "valid_rows",
        "duplicate_rows",
        "status",
    )
    ordering = ("-created_at",)
    filter_backends = (DjangoFilterBackend, SearchFilter, NullsLastOrderingFilter)

    def get_serializer_class(self):
        if self.action in {"retrieve", "upload", "mapping", "start", "preview"}:
            return ImportJobDetailSerializer
        return ImportJobSerializer

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _refresh_analysis(job: ImportJob, mapping: dict[str, str | None] | None = None) -> None:
        """Re-run the one-pass analysis and cache it on the job."""
        analysis = analyze_file(
            job.upload.path,
            file_type=job.file_type,
            sheet=job.selected_sheet or None,
            mapping=mapping,
        )
        job.analysis = analysis.as_dict()
        job.headers = list(analysis.mapping.keys())
        job.column_mapping = analysis.mapping
        job.total_rows = analysis.total_rows
        job.save(
            update_fields=["analysis", "headers", "column_mapping", "total_rows", "updated_at"]
        )

    def _require_file(self, job: ImportJob) -> None:
        if not job.upload or not job.upload.name:
            raise Http404("This import has no stored file.")

    # -------------------------------------------------------------------- CRUD
    def retrieve(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_object()).data)

    def destroy(self, request, *args, **kwargs):
        """Discard a job: the row, the issues and the stored file."""
        job = self.get_object()
        if job.status == ImportStatus.PROCESSING:
            return Response(
                {"error": {"code": "conflict", "message": "The import is running.", "details": {}}},
                status=http_status.HTTP_409_CONFLICT,
            )
        self._delete_file(job)
        job.delete()
        return Response(status=http_status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _delete_file(job: ImportJob) -> None:
        if job.upload:
            job.upload.delete(save=False)

    # ------------------------------------------------------------------ actions
    @extend_schema(request=UploadSerializer, responses={201: ImportJobDetailSerializer})
    @action(
        detail=False,
        methods=["post"],
        url_path="upload",
        parser_classes=(MultiPartParser, FormParser),
    )
    def upload(self, request):
        """Store the upload, analyse it once and return the preview payload."""
        serializer = UploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = serializer.validated_data["file"]
        sheet = serializer.validated_data.get("sheet", "")

        file_type = detect_file_type(upload.name)
        job = ImportJob(
            filename=upload.name[:255],
            upload=upload,
            file_type=file_type,
            file_size=upload.size,
            status=ImportStatus.QUEUED,
        )
        job.save()

        try:
            info = describe_file(job.upload.path, file_type)
            sheets = info.get("sheets", [])
            if sheet and sheet in sheets:
                job.selected_sheet = sheet
            elif sheets:
                job.selected_sheet = sheets[0]

            job.encoding = info.get("encoding", "")
            job.delimiter = info.get("delimiter", "")
            job.sheet_names = list(sheets)

            headers = header_row(job.upload.path, file_type, sheet=job.selected_sheet or None)
            if not headers:
                raise MappingError("The file has no header row.")
            job.headers = headers

            matches = detect_mapping(headers)
            job.column_mapping = {match.column: match.field for match in matches}
            job.save(
                update_fields=[
                    "selected_sheet",
                    "encoding",
                    "delimiter",
                    "sheet_names",
                    "headers",
                    "column_mapping",
                    "updated_at",
                ]
            )
            self._refresh_analysis(job)
        except (MappingError, UnsupportedFileType, OSError, ValueError) as exc:
            self._delete_file(job)
            job.delete()
            return Response(
                {
                    "error": {
                        "code": "invalid_file",
                        "message": str(exc) or "The file could not be read.",
                        "details": {},
                    }
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        job.refresh_from_db()
        return Response(
            self.get_serializer(job).data,
            status=http_status.HTTP_201_CREATED,
        )

    @extend_schema(responses={200: None}, summary="Import system-field catalog")
    @action(detail=False, methods=["get"], url_path="fields")
    def fields(self, request):
        """Every field the mapper can target, with labels and aliases."""
        return Response({"system_fields": system_fields_payload()})

    @extend_schema(responses={200: None}, summary="Imports module status")
    @action(detail=False, methods=["get"], url_path="status")
    def module_status(self, request):
        totals = ImportJob.objects.aggregate(
            imports=Sum("valid_rows"),
            duplicates=Sum("duplicate_rows"),
            invalid=Sum("invalid_rows"),
        )
        return Response(
            {
                "module": "imports",
                "status": "implemented",
                "phase": 3,
                "supported_files": ["csv", "xlsx"],
                "jobs": ImportJob.objects.count(),
                "imported_rows": totals["imports"] or 0,
                "duplicate_rows": totals["duplicates"] or 0,
                "invalid_rows": totals["invalid"] or 0,
            }
        )

    @extend_schema(responses={200: ImportJobDetailSerializer}, summary="Preview an upload")
    @action(detail=True, methods=["get"], url_path="preview")
    def preview(self, request, pk=None):
        job = self.get_object()
        self._require_file(job)
        return Response(self.get_serializer(job).data["preview"])

    @extend_schema(request=StartImportSerializer, responses={200: ImportJobDetailSerializer})
    @action(detail=True, methods=["post", "patch"], url_path="mapping")
    def mapping(self, request, pk=None):
        """Apply a manually edited mapping and refresh the preview numbers."""
        job = self.get_object()
        self._require_file(job)
        serializer = StartImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        headers = list(job.headers or [])
        if not headers:
            headers = header_row(job.upload.path, job.file_type, sheet=job.selected_sheet or None)

        submitted = serializer.validated_data.get("column_mapping")
        if submitted is None:
            # No explicit mapping: re-run auto-detection.
            submitted = {match.column: match.field for match in detect_mapping(headers)}

        try:
            plan = build_plan(headers, submitted)
        except MappingError as exc:
            return Response(
                {"error": {"code": "invalid_mapping", "message": str(exc), "details": {}}},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        self._refresh_analysis(job, mapping=plan.column_mapping())
        job.refresh_from_db()
        return Response(self.get_serializer(job).data)

    @extend_schema(request=StartImportSerializer, responses={202: ImportJobDetailSerializer})
    @action(detail=True, methods=["post"], url_path="start")
    def start(self, request, pk=None):
        """Confirm the mapping and hand the file to the background worker."""
        job = self.get_object()
        self._require_file(job)

        if job.status == ImportStatus.PROCESSING:
            return Response(
                {
                    "error": {
                        "code": "conflict",
                        "message": "The import is already running.",
                        "details": {},
                    }
                },
                status=http_status.HTTP_409_CONFLICT,
            )
        if job.status == ImportStatus.COMPLETED:
            return Response(
                {
                    "error": {
                        "code": "conflict",
                        "message": "This import has already completed.",
                        "details": {},
                    }
                },
                status=http_status.HTTP_409_CONFLICT,
            )

        serializer = StartImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        headers = list(job.headers or [])
        submitted = serializer.validated_data.get("column_mapping") or job.column_mapping or {}
        try:
            plan = build_plan(headers, submitted)
        except MappingError as exc:
            return Response(
                {"error": {"code": "invalid_mapping", "message": str(exc), "details": {}}},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        if not plan.has("company_name"):
            return Response(
                {
                    "error": {
                        "code": "invalid_mapping",
                        "message": "Map one column to “Business name” before importing.",
                        "details": {},
                    }
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        job.column_mapping = plan.column_mapping()
        if serializer.validated_data.get("sheet"):
            job.selected_sheet = serializer.validated_data["sheet"]
        job.status = ImportStatus.QUEUED
        job.error_message = ""
        job.save(
            update_fields=[
                "column_mapping",
                "selected_sheet",
                "status",
                "error_message",
                "updated_at",
            ]
        )

        mode = enqueue_import_job(job)
        job.refresh_from_db()
        payload = self.get_serializer(job).data
        payload["dispatch"] = mode
        return Response(payload, status=http_status.HTTP_202_ACCEPTED)

    @extend_schema(responses={200: ImportJobSerializer}, summary="Import progress")
    @action(detail=True, methods=["get"], url_path="status")
    def progress(self, request, pk=None):
        """Small payload for the progress poller."""
        job = self.get_object()
        return Response(ImportJobSerializer(job).data)

    @extend_schema(responses={204: None}, summary="Discard an upload")
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        return self.destroy(request, pk=pk)
