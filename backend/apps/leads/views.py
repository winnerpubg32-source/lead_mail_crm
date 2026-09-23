"""
Leads API (Phase 5).

``GET    /api/v1/leads/``                paginated, searchable, filterable list
``GET    /api/v1/leads/{id}/``           detail (with notes, timeline, score breakdown)
``PATCH  /api/v1/leads/{id}/``           update status / score / source
``POST   /api/v1/leads/{id}/notes/``     add a note
``POST   /api/v1/leads/{id}/rescore/``   recompute score
``POST   /api/v1/leads/bulk-action/``    bulk status / industry / campaign / suppress
``GET    /api/v1/leads/export/``         CSV export (respects filters)
``GET    /api/v1/leads/statuses/``       enum vocabulary
"""

from __future__ import annotations

from django.db.models import Count
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.leads.activity_models import ActivityType, LeadActivity, LeadNote
from apps.leads.filters import LeadFilter
from apps.leads.models import EmailStatus, Lead, LeadStatus
from apps.leads.scoring import (
    POINTS,
    ScoreClassification,
    classify_score,
    compute_lead_score,
    rescore_leads,
)
from apps.leads.serializers import (
    BulkActionSerializer,
    LeadActivitySerializer,
    LeadDetailSerializer,
    LeadListSerializer,
    LeadNoteCreateSerializer,
    LeadNoteSerializer,
    LeadSerializer,
    LeadUpdateSerializer,
    status_choices,
)
from apps.leads.services import (
    annotate_lead_list,
    apply_bulk_action,
    export_leads_csv,
    record_activity,
    record_note,
)


@extend_schema_view(
    list=extend_schema(summary="List leads", tags=["leads"]),
    retrieve=extend_schema(summary="Retrieve a lead", tags=["leads"]),
    update=extend_schema(summary="Update a lead", tags=["leads"]),
    partial_update=extend_schema(summary="Patch a lead", tags=["leads"]),
    statuses=extend_schema(summary="Lead + e-mail status vocabulary", tags=["leads"]),
)
class LeadViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (AllowAny,)
    filterset_class = LeadFilter
    search_fields = (
        "company__name",
        "company__normalized_name",
        "company__normalized_website",
        "company__sub_industry",
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
        "company__industry",
        "company__sub_industry",
        "contact__full_name",
        "company__state",
        "company__city",
        "created_at",
        "updated_at",
        "last_contact_at",
    )
    ordering = ("-lead_score", "-created_at")

    def get_queryset(self):
        qs = Lead.objects.select_related("company", "contact")
        if self.action == "retrieve":
            qs = qs.prefetch_related(
                "notes", "activities"
            )
        if self.request.query_params.get("include_merged") != "true":
            qs = qs.exclude(lead_status=LeadStatus.MERGED)
        if self.action == "list":
            qs = annotate_lead_list(qs)
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LeadDetailSerializer
        if self.action in ("update", "partial_update"):
            return LeadUpdateSerializer
        if self.action == "list":
            return LeadListSerializer
        return LeadSerializer

    @action(detail=True, methods=["post"], url_path="notes")
    def add_note(self, request, pk=None):
        lead = self.get_object()
        serializer = LeadNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = LeadNote.objects.create(
            lead=lead,
            body=serializer.validated_data["body"],
            pinned=serializer.validated_data.get("pinned", False),
        )
        record_note(note, actor="api")
        return Response(LeadNoteSerializer(note).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="timeline")
    def timeline(self, request, pk=None):
        lead = self.get_object()
        activities = lead.activities.all()[:200]
        return Response(LeadActivitySerializer(activities, many=True).data)

    @action(detail=True, methods=["post"], url_path="rescore")
    def rescore(self, request, pk=None):
        lead = self.get_object()
        score, components = compute_lead_score(lead)
        old_score = lead.lead_score
        lead.lead_score = score
        lead.save(update_fields=["lead_score", "updated_at"])
        if old_score != score:
            record_activity(
                lead,
                ActivityType.SCORE_CHANGE,
                title=f"Score recomputed: {old_score} → {score}",
                metadata={"old_score": old_score, "new_score": score, "components": components.as_dict()},
                actor="api",
            )
        return Response(
            {
                "lead_score": score,
                "classification": classify_score(score, lead.email_status),
                "components": components.as_dict(),
            }
        )

    @action(detail=False, methods=["post"], url_path="rescore-all")
    def rescore_all(self, request):
        updated = rescore_leads()
        return Response({"status": "ok", "updated": updated})

    @action(detail=False, methods=["post"], url_path="bulk-action")
    def bulk_action(self, request):
        serializer = BulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        summary = apply_bulk_action(data["ids"], data["action"], **{k: v for k, v in data.items() if k not in ("ids", "action")})
        return Response(summary, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        """CSV export of the currently filtered leads."""
        qs = self.filter_queryset(self.get_queryset())
        return export_leads_csv(qs)

    @action(detail=False, methods=["get"], url_path="filters")
    def filter_options(self, request):
        """Distinct values for industry / city / state / source filters."""
        from django.db.models.functions import Lower

        def distinct_values(field):
            return list(
                Lead.objects.exclude(lead_status=LeadStatus.MERGED)
                .exclude(**{f"{field}__isnull": True})
                .values_list(field, flat=True)
                .distinct()
                .order_by(Lower(field))[:200]
            )

        return Response(
            {
                "industries": [v for v in distinct_values("company__industry") if v],
                "sub_industries": [v for v in distinct_values("company__sub_industry") if v],
                "cities": [v for v in distinct_values("company__city") if v],
                "states": [v for v in distinct_values("company__state") if v],
                "sources": [v for v in distinct_values("source") if v],
                "score_points": POINTS,
            }
        )

    @action(detail=False, methods=["get"], url_path="statuses")
    def statuses(self, request):
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
        # Score classification counts — computed in Python to stay DB-agnostic.
        score_counts: dict[str, int] = {c: 0 for c in ScoreClassification.values}
        for lead in base.only("lead_score", "email_status").iterator(chunk_size=500):
            code = classify_score(lead.lead_score, lead.email_status)
            score_counts[code] = score_counts.get(code, 0) + 1
        payload["score_classification_counts"] = score_counts
        payload["total"] = base.count()
        payload["defaults"] = {"lead_status": LeadStatus.NEW, "email_status": EmailStatus.UNKNOWN}
        payload["score_points"] = POINTS
        return Response(payload)

    def perform_update(self, serializer):
        lead = self.get_object()
        old_status = lead.lead_status
        old_email_status = lead.email_status
        old_score = lead.lead_score
        instance = serializer.save()
        # Log status change.
        if "lead_status" in serializer.validated_data and instance.lead_status != old_status:
            record_activity(
                instance,
                ActivityType.STATUS_CHANGE,
                title=f"Status set to {instance.get_lead_status_display()}",
                metadata={"old_status": old_status, "new_status": instance.lead_status},
                actor="api",
            )
        if "email_status" in serializer.validated_data and instance.email_status != old_email_status:
            record_activity(
                instance,
                ActivityType.MANUAL_EDIT,
                title=f"E-mail status set to {instance.get_email_status_display()}",
                metadata={"old_status": old_email_status, "new_status": instance.email_status},
                actor="api",
            )
        # Rescore after the edit so the score matches the new state.
        new_score, _ = compute_lead_score(instance)
        if new_score != instance.lead_score:
            instance.lead_score = new_score
            instance.save(update_fields=["lead_score"])
        if instance.lead_score != old_score:
            record_activity(
                instance,
                ActivityType.SCORE_CHANGE,
                title=f"Score changed: {old_score} → {instance.lead_score}",
                metadata={"old_score": old_score, "new_score": instance.lead_score},
                actor="api",
            )
