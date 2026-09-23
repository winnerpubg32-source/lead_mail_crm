"""
Companies API.

``GET /api/v1/companies/``      — paginated, searchable, filterable list
``GET /api/v1/companies/{id}/`` — detail
"""

from __future__ import annotations

from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.companies.filters import CompanyFilter
from apps.companies.models import Company
from apps.companies.serializers import CompanyListSerializer, CompanySerializer
from core.filters import NullsLastOrderingFilter


class NullsLastCompanyOrdering(NullsLastOrderingFilter):
    """Companies with no employee count sort last, not first."""

    nulls_last_fields = ("employee_count",)


@extend_schema_view(
    list=extend_schema(summary="List companies", tags=["companies"]),
    retrieve=extend_schema(summary="Retrieve a company", tags=["companies"]),
    status=extend_schema(summary="Companies module status", tags=["companies"]),
)
class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only company endpoints.

    Writing arrives with the import phase, which owns dedup rules and bulk
    ingestion — exposing POST/PATCH before those exist would let the database
    drift away from its normalisation rules.
    """

    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend, SearchFilter, NullsLastCompanyOrdering)
    filterset_class = CompanyFilter
    search_fields = ("name", "normalized_name", "normalized_website", "industry", "city", "state")
    ordering_fields = (
        "name",
        "industry",
        "city",
        "state",
        "employee_count",
        "lead_count",
        "contact_count",
        "created_at",
        "updated_at",
    )
    ordering = ("name",)

    def get_queryset(self):
        queryset = Company.objects.annotate(
            lead_count=Count("leads", distinct=True),
            contact_count=Count("contacts", distinct=True),
        )
        # list and detail share the queryset; only the serialiser differs.
        if self.action == "list":
            return queryset.only(
                "id",
                "name",
                "industry",
                "sub_industry",
                "website",
                "normalized_website",
                "phone",
                "city",
                "state",
                "country",
                "employee_count",
                "source",
                "created_at",
                "updated_at",
            )
        return queryset

    def get_serializer_class(self):
        return CompanyListSerializer if self.action == "list" else CompanySerializer

    @action(detail=False, methods=["get"], url_path="status")
    def status(self, request):
        """Module summary — used by smoke tests and the dashboard's data-source card."""
        return Response(
            {
                "module": "companies",
                "status": "implementation_started",
                "phase": 2,
                "total": Company.objects.count(),
                "filters": sorted(CompanyFilter.base_filters),
            }
        )
