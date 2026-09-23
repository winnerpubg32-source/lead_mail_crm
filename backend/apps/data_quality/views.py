"""
Data-quality API (Phase 4).

Endpoints
---------
``GET    /api/v1/data-quality/stats/``                dashboard counters
``GET    /api/v1/data-quality/duplicates/``           list open duplicate groups
``GET    /api/v1/data-quality/duplicates/{id}/``      detail
``POST   /api/v1/data-quality/duplicates/{id}/merge/``  merge the two leads
``POST   /api/v1/data-quality/duplicates/{id}/keep-both/`` mark as not duplicates
``POST   /api/v1/data-quality/duplicates/{id}/ignore/``  ignore this pair
``POST   /api/v1/data-quality/duplicates/detect/``    kick off a duplicate scan
``GET    /api/v1/data-quality/missing-email/``        list leads without email
``GET    /api/v1/data-quality/merges/``               merge audit log
``POST   /api/v1/data-quality/backfill/``             re-run normalization (admin)
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.data_quality.models import (
    MATCH_CONFIDENCE,
    DuplicateGroup,
    DuplicateStatus,
    MergeAudit,
)
from apps.data_quality.serializers import (
    DataQualityStatsSerializer,
    DuplicateGroupSerializer,
    MergeAuditSerializer,
    MergeRequestSerializer,
    MissingEmailLeadSerializer,
    ResolveRequestSerializer,
)
from apps.data_quality.services import (
    backfill_normalization,
    compute_data_quality_stats,
    detect_duplicates,
    find_missing_email_leads,
    ignore_group,
    keep_both_group,
    merge_leads,
)
from apps.leads.models import Lead
from core.pagination import DefaultPagination


@extend_schema(tags=["data-quality"])
class DataQualityRootView(APIView):
    """Module status stub — used by smoke tests to prove the route is live."""

    permission_classes = (AllowAny,)

    def get(self, request):
        return Response(
            {
                "module": "data_quality",
                "status": "ok",
                "phase": 4,
                "match_reasons": [
                    {"code": code, "confidence": conf} for code, conf in MATCH_CONFIDENCE.items()
                ],
            }
        )


@extend_schema(tags=["data-quality"])
class DataQualityStatsView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(summary="Data quality statistics", responses=DataQualityStatsSerializer)
    def get(self, request):
        stats = compute_data_quality_stats()
        serializer = DataQualityStatsSerializer(stats)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary="List duplicate groups", tags=["data-quality"]),
    retrieve=extend_schema(summary="Retrieve a duplicate group", tags=["data-quality"]),
)
class DuplicateGroupViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    permission_classes = (AllowAny,)
    serializer_class = DuplicateGroupSerializer
    pagination_class = DefaultPagination
    filterset_fields = ("status", "reason_code")

    def get_queryset(self):
        return (
            DuplicateGroup.objects.prefetch_related(
                "members", "members__lead", "members__lead__company", "members__lead__contact"
            )
            .all()
            .order_by("-confidence", "-created_at")
        )

    @action(detail=False, methods=["post"], url_path="detect")
    def detect(self, request):
        """Run the duplicate detector and return counts of new groups."""
        clear = bool(request.data.get("clear_existing", False))
        result = detect_duplicates(clear_existing=clear)
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="merge")
    def merge(self, request, pk=None):
        """Merge two leads in this group: winner survives, loser becomes MERGED."""
        group = self.get_object()
        if group.status != DuplicateStatus.OPEN:
            return Response(
                {"error": f"Group is already {group.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        members = list(group.members.select_related("lead").all())
        if len(members) != 2:
            return Response(
                {"error": "Merge is only supported for 2-record groups."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = MergeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        winner_id = serializer.validated_data["winner"]
        loser_id = serializer.validated_data["loser"]

        member_ids = {m.lead_id for m in members}
        if winner_id not in member_ids or loser_id not in member_ids:
            return Response(
                {"error": "Both winner and loser must belong to this duplicate group."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        audit = merge_leads(winner_id, loser_id, group=group, performed_by="api")
        return Response(MergeAuditSerializer(audit).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="keep-both")
    def keep_both(self, request, pk=None):
        input_ = ResolveRequestSerializer(data=request.data or {})
        input_.is_valid(raise_exception=True)
        group = keep_both_group(int(pk), performed_by=input_.validated_data.get("performed_by", ""))
        return Response(DuplicateGroupSerializer(group).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="ignore")
    def ignore(self, request, pk=None):
        input_ = ResolveRequestSerializer(data=request.data or {})
        input_.is_valid(raise_exception=True)
        group = ignore_group(int(pk), performed_by=input_.validated_data.get("performed_by", ""))
        return Response(DuplicateGroupSerializer(group).data, status=status.HTTP_200_OK)


@extend_schema(tags=["data-quality"])
class MissingEmailViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    serializer_class = MissingEmailLeadSerializer
    pagination_class = DefaultPagination
    search_fields = (
        "company__name",
        "company__normalized_website",
        "company__city",
        "company__state",
        "company__industry",
        "contact__full_name",
        "source",
        "source_file",
    )
    filterset_fields = ("company__industry", "company__city", "company__state", "source")

    def get_queryset(self):
        return find_missing_email_leads()


@extend_schema(tags=["data-quality"])
class MergeAuditViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    serializer_class = MergeAuditSerializer
    pagination_class = DefaultPagination
    queryset = MergeAudit.objects.select_related(
        "surviving_lead", "surviving_lead__company", "surviving_lead__contact", "merged_lead"
    ).order_by("-created_at")


@extend_schema(tags=["data-quality"])
class BackfillView(APIView):
    """Re-run normalization across existing records (admin utility)."""

    permission_classes = (AllowAny,)

    def post(self, request):
        counts = backfill_normalization()
        return Response({"status": "ok", "counts": counts})
