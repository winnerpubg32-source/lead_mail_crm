"""Filtering for ``GET /api/v1/companies/``."""

from __future__ import annotations

import django_filters as filters

from apps.companies.models import Company


class CompanyFilter(filters.FilterSet):
    """Field-level filters; text search and ordering are handled by DRF."""

    industry = filters.CharFilter(field_name="industry", lookup_expr="iexact")
    state = filters.CharFilter(field_name="state", lookup_expr="iexact")
    city = filters.CharFilter(field_name="city", lookup_expr="iexact")
    country = filters.CharFilter(field_name="country", lookup_expr="iexact")
    source = filters.CharFilter(field_name="source", lookup_expr="iexact")
    domain = filters.CharFilter(field_name="normalized_website", lookup_expr="iexact")

    employee_count_min = filters.NumberFilter(field_name="employee_count", lookup_expr="gte")
    employee_count_max = filters.NumberFilter(field_name="employee_count", lookup_expr="lte")

    has_website = filters.BooleanFilter(method="filter_has_website")
    created_after = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Company
        fields = (
            "industry",
            "state",
            "city",
            "country",
            "source",
            "domain",
            "employee_count_min",
            "employee_count_max",
            "has_website",
        )

    def filter_has_website(self, queryset, name: str, value: bool):
        if value:
            return queryset.exclude(normalized_website="")
        return queryset.filter(normalized_website="")
