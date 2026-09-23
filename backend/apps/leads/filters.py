"""Filtering for ``GET /api/v1/leads/`` (Phase 5)."""

from __future__ import annotations

import django_filters as filters
from django.db.models import Q

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.leads.models import EmailStatus, Lead, LeadStatus
from apps.leads.scoring import ScoreClassification
from core.filters import csv_multiple_choice_filter


class LeadFilter(filters.FilterSet):
    """
    Field-level filters.

    Multi-value filters accept repeated query parameters
    (``?lead_status=NEW&lead_status=QUALIFIED``) or a comma separated list.
    """

    lead_status = csv_multiple_choice_filter(choices=LeadStatus.choices)
    email_status = csv_multiple_choice_filter(choices=EmailStatus.choices)
    source = filters.CharFilter(field_name="source", lookup_expr="iexact")
    score_classification = filters.CharFilter(method="filter_score_classification")

    company = filters.ModelChoiceFilter(queryset=Company.objects.all(), field_name="company")
    contact = filters.ModelChoiceFilter(queryset=Contact.objects.all(), field_name="contact")

    industry = filters.CharFilter(field_name="company__industry", lookup_expr="iexact")
    # Sub-industry is exact-substring-insensitive (free-text on the company).
    sub_industry = filters.CharFilter(field_name="company__sub_industry", lookup_expr="icontains")
    city = filters.CharFilter(field_name="company__city", lookup_expr="iexact")
    state = filters.CharFilter(field_name="company__state", lookup_expr="iexact")
    country = filters.CharFilter(field_name="company__country", lookup_expr="iexact")

    min_score = filters.NumberFilter(field_name="lead_score", lookup_expr="gte")
    max_score = filters.NumberFilter(field_name="lead_score", lookup_expr="lte")

    has_email = filters.BooleanFilter(method="filter_has_email")
    has_website = filters.BooleanFilter(method="filter_has_website")
    is_contactable = filters.BooleanFilter(method="filter_is_contactable")
    created_after = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Lead
        fields = (
            "lead_status",
            "email_status",
            "score_classification",
            "source",
            "company",
            "contact",
            "industry",
            "sub_industry",
            "city",
            "state",
            "country",
            "min_score",
            "max_score",
            "has_email",
            "has_website",
            "is_contactable",
        )

    def filter_has_email(self, queryset, name: str, value: bool):
        if value:
            return queryset.exclude(contact__normalized_email="")
        return queryset.filter(Q(contact__isnull=True) | Q(contact__normalized_email=""))

    def filter_has_website(self, queryset, name: str, value: bool):
        if value:
            return queryset.exclude(
                Q(company__isnull=True) | Q(company__normalized_website="")
            )
        return queryset.filter(
            Q(company__isnull=True) | Q(company__normalized_website="")
        )

    def filter_score_classification(self, queryset, name: str, value: str):
        # Map the code -> numeric bands (see scoring.classify_score).
        bands = {
            "HOT": (70, 10_000),
            "WARM": (50, 69),
            "COLD": (20, 49),
            "UNQUALIFIED": (0, 19),
        }
        if value not in bands:
            return queryset
        lo, hi = bands[value]
        blocked = [
            EmailStatus.INVALID,
            EmailStatus.BOUNCED,
            EmailStatus.UNSUBSCRIBED,
            EmailStatus.SUPPRESSED,
        ]
        if value == "UNQUALIFIED":
            return queryset.filter(
                Q(lead_score__lt=20) | Q(email_status__in=blocked)
            )
        return queryset.filter(lead_score__gte=lo, lead_score__lte=hi).exclude(
            email_status__in=blocked
        )

    def filter_is_contactable(self, queryset, name: str, value: bool):
        blocked = [
            EmailStatus.INVALID,
            EmailStatus.BOUNCED,
            EmailStatus.UNSUBSCRIBED,
            EmailStatus.SUPPRESSED,
        ]
        if value:
            return queryset.exclude(contact__normalized_email="").exclude(email_status__in=blocked)
        return queryset.filter(Q(email_status__in=blocked) | Q(contact__normalized_email=""))
