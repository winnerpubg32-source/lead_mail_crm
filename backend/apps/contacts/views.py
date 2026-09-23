"""
Contacts API.

``GET /api/v1/contacts/``      — paginated, searchable, filterable list
``GET /api/v1/contacts/{id}/`` — detail
"""

from __future__ import annotations

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.contacts.filters import ContactFilter
from apps.contacts.models import Contact
from apps.contacts.serializers import ContactListSerializer, ContactSerializer
from core.filters import NullsLastOrderingFilter


class NullsLastContactOrdering(NullsLastOrderingFilter):
    """Contacts without a company sort last when ordering by company."""

    nulls_last_fields = ("company__name",)


@extend_schema_view(
    list=extend_schema(summary="List contacts", tags=["contacts"]),
    retrieve=extend_schema(summary="Retrieve a contact", tags=["contacts"]),
    status=extend_schema(summary="Contacts module status", tags=["contacts"]),
)
class ContactViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only contact endpoints (writes arrive with the import phase)."""

    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend, SearchFilter, NullsLastContactOrdering)
    filterset_class = ContactFilter
    search_fields = (
        "first_name",
        "last_name",
        "full_name",
        "job_title",
        "email",
        "normalized_email",
        "company__name",
    )
    ordering_fields = (
        "full_name",
        "last_name",
        "first_name",
        "job_title",
        "email",
        "company__name",
        "created_at",
        "updated_at",
    )
    ordering = ("full_name",)

    def get_queryset(self):
        return Contact.objects.select_related("company")

    def get_serializer_class(self):
        return ContactListSerializer if self.action == "list" else ContactSerializer

    @action(detail=False, methods=["get"], url_path="status")
    def status(self, request):
        """Module summary — used by smoke tests and the dashboard's data-source card."""
        return Response(
            {
                "module": "contacts",
                "status": "implementation_started",
                "phase": 2,
                "total": Contact.objects.count(),
                "filters": sorted(ContactFilter.base_filters),
            }
        )
