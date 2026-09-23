"""Filters for ``GET /api/v1/campaigns/`` (Phase 6)."""

from __future__ import annotations

import django_filters as filters
from django.db.models import Q

from apps.campaigns.models import Campaign, CampaignStatus
from core.filters import CsvMultipleChoiceFilter


class CampaignFilter(filters.FilterSet):
    status = CsvMultipleChoiceFilter(choices=CampaignStatus.choices)
    industry = filters.CharFilter(field_name="industry", lookup_expr="iexact")
    search = filters.CharFilter(method="filter_search")
    has_template = filters.BooleanFilter(method="filter_has_template")

    class Meta:
        model = Campaign
        fields = ("status", "industry", "template")

    def filter_search(self, queryset, name: str, value: str):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(recommended_service__icontains=value)
        )

    def filter_has_template(self, queryset, name: str, value: bool):
        if value:
            return queryset.exclude(template__isnull=True)
        return queryset.filter(template__isnull=True)
