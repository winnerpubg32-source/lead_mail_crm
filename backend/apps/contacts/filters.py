"""Filtering for ``GET /api/v1/contacts/``."""

from __future__ import annotations

import django_filters as filters

from apps.companies.models import Company
from apps.contacts.models import Contact, PhoneType


class ContactFilter(filters.FilterSet):
    """Field-level filters; text search and ordering are handled by DRF."""

    company = filters.ModelChoiceFilter(queryset=Company.objects.all(), field_name="company")
    job_title = filters.CharFilter(field_name="job_title", lookup_expr="icontains")
    phone_type = filters.ChoiceFilter(choices=PhoneType.choices)
    city = filters.CharFilter(field_name="company__city", lookup_expr="iexact")
    state = filters.CharFilter(field_name="company__state", lookup_expr="iexact")
    industry = filters.CharFilter(field_name="company__industry", lookup_expr="iexact")
    source = filters.CharFilter(method="filter_by_source")
    has_email = filters.BooleanFilter(method="filter_has_email")
    created_after = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Contact
        fields = ("company", "job_title", "phone_type", "city", "state", "industry", "has_email")

    def filter_has_email(self, queryset, name: str, value: bool):
        if value:
            return queryset.exclude(normalized_email="")
        return queryset.filter(normalized_email="")

    def filter_by_source(self, queryset, name: str, value: str):
        """Contacts carry no source column — it lives on the company they belong to."""
        return queryset.filter(company__source__iexact=value)
