"""Filtering, search and ordering for the import history."""

from __future__ import annotations

import django_filters as filters

from apps.imports.models import ImportJob


class ImportJobFilter(filters.FilterSet):
    """History filters: status, file type, e-mail coverage and date range."""

    status = filters.CharFilter(field_name="status", lookup_expr="iexact")
    file_type = filters.CharFilter(field_name="file_type", lookup_expr="iexact")
    with_errors = filters.BooleanFilter(method="filter_with_errors")
    created_after = filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = ImportJob
        fields = ("status", "file_type", "with_errors", "created_after", "created_before")

    def filter_with_errors(self, queryset, name: str, value: bool):
        if value is None:
            return queryset
        if value:
            return queryset.filter(error_rows__gt=0) | queryset.filter(status="FAILED")
        return queryset.filter(error_rows=0).exclude(status="FAILED")
