"""
Leads API.

``GET /api/v1/leads/``            — paginated, searchable, filterable list
``GET /api/v1/leads/{id}/``       — detail
``GET /api/v1/leads/statuses/``   — enum vocabulary for the UI filters
"""

from __future__ import annotations

from django.db.models import Count
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.leads.filters import LeadFilter
from apps.leads.models import EmailStatus, Lead, LeadStatus
from apps.leads.serializers import LeadListSerializer, LeadSerializer, status_choices


@extend_schema_view(
    list=extend_schema(summary="List leads", tags=["leads"]),
    retrieve=extend_schema(summary="Retrieve a lead", tags=["leads"]),
    statuses=extend_schema(summary="Lead + e-mail status vocabulary", tags=["leads"]),
)
class LeadViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only lead endpoints.

    The table's columns come from the company/contact relations, so the
    queryset is always joined to avoid N+1 queries.
    """

    permission_classes = (AllowAny,)
    filterset_class = LeadFilter
    search_fields = (
        "company__name",
        "company__normalized_name",
        "company__normalized_website",
        "contact__full_name",
        "contact__email",
        "contact__job_title",
        "source",
        "source_file",
    )
    ordering_fields = (
        "lead_score",
        "lead_status",
        "email_status",
        "company__name",
        "contact__full_name",
        "created_at",
        "updated_at",
    )
    ordering = ("-lead_score", "-created_at")

    def get_queryset(self):
        # By default hide merged records so they don't pollute the pipeline.
        # Callers can pass ``?include_merged=true`` or filter explicitly to
        # retrieve them.
        qs = Lead.objects.select_related("company", "contact")
        if self.request.query_params.get("include_merged") != "true":
            qs = qs.exclude(lead_status=LeadStatus.MERGED)
        return qs

    def get_serializer_class(self):
        return LeadListSerializer if self.action == "list" else LeadSerializer

    @action(detail=False, methods=["get"], url_path="statuses")
    def statuses(self, request):
        """Enum values + labels, plus counts per status for the filter chips."""
        base = Lead.objects.exclude(lead_status=LeadStatus.MERGED)
        counts = {
            row["lead_status"]: row["total"]
            for row in base.values("lead_status").annotate(total=Count("id"))
        }
        email_counts = {
            row["email_status"]: row["total"]
            for row in base.values("email_status").annotate(total=Count("id"))
        }
        payload = status_choices()
        for entry in payload["lead_status"]:
            entry["count"] = counts.get(entry["value"], 0)
        for entry in payload["email_status"]:
            entry["count"] = email_counts.get(entry["value"], 0)
        payload["total"] = base.count()
        payload["defaults"] = {"lead_status": LeadStatus.NEW, "email_status": EmailStatus.UNKNOWN}
        return Response(payload)
