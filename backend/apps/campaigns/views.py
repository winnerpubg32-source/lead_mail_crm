"""
Campaigns API (Phase 6).

``GET    /api/v1/campaigns/``              list (search/filter/sort/paginate)
``POST   /api/v1/campaigns/``              create (DRAFT)
``GET    /api/v1/campaigns/{id}/``         detail (with template + membership count)
``PATCH   /api/v1/campaigns/{id}/``        update campaign (wizard saves)
``DELETE  /api/v1/campaigns/{id}/``        cancel & delete
``POST   /api/v1/campaigns/{id}/status/``  transition status (READY / RUNNING / PAUSED / COMPLETED / CANCELLED)
``POST   /api/v1/campaigns/{id}/prepare/`` snapshot audience (pre-flight; same as moving to READY)
``GET    /api/v1/campaigns/{id}/preview-audience/`` eligible leads preview (paginated)
``GET    /api/v1/campaigns/{id}/members/`` campaign members (paginated)
``GET    /api/v1/campaigns/statuses/``     enum vocabulary
"""

from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.campaigns.filters import CampaignFilter
from apps.campaigns.models import Campaign, CampaignLead, CampaignStatus
from apps.campaigns.serializers import (
    CampaignDetailSerializer,
    CampaignListSerializer,
    CampaignSerializer,
    CampaignStatusActionSerializer,
    status_vocabulary,
)
from apps.campaigns.services import (
    count_eligible_leads,
    eligible_leads_qs,
    prepare_campaign,
    transition_campaign,
    validate_campaign_for_launch,
)
from apps.leads.models import Lead
from apps.leads.serializers import LeadListSerializer


class CampaignsPingView(APIView):
    """Backward-compat module-ping endpoint."""

    authentication_classes: tuple = ()
    permission_classes: tuple = (AllowAny,)

    def get(self, request):
        return Response({"module": "campaigns", "status": "live", "phase": 6})


@extend_schema_view(
    list=extend_schema(summary="List campaigns", tags=["campaigns"]),
    retrieve=extend_schema(summary="Retrieve a campaign", tags=["campaigns"]),
    create=extend_schema(summary="Create a campaign (draft)", tags=["campaigns"]),
    update=extend_schema(summary="Replace a campaign", tags=["campaigns"]),
    partial_update=extend_schema(summary="Patch a campaign (wizard save)", tags=["campaigns"]),
    destroy=extend_schema(summary="Cancel and delete a campaign", tags=["campaigns"]),
)
class CampaignViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (AllowAny,)
    filterset_class = CampaignFilter
    search_fields = ("name", "description", "recommended_service")
    ordering_fields = (
        "name",
        "status",
        "created_at",
        "updated_at",
        "daily_limit",
        "sent_count",
        "reply_count",
        "eligible_count",
        "scheduled_start_at",
    )
    ordering = ("-updated_at",)

    def get_queryset(self):
        qs = Campaign.objects.select_related("template")
        if self.action == "list":
            # Live-audience-size annotation uses a subquery to keep the list page
            # efficient; drafts compute live, READY+ rows use their cached count.
            qs = qs.annotate(
                _members_count=Count("memberships", distinct=True),
            )
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CampaignDetailSerializer
        if self.action == "list":
            return CampaignListSerializer
        return CampaignSerializer

    def perform_destroy(self, instance):
        # Hard-delete only drafts/cancelled; running campaigns must be cancelled first.
        if instance.status in (CampaignStatus.RUNNING, CampaignStatus.PAUSED):
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                f"Pause or cancel the campaign before deleting it (currently {instance.status})."
            )
        instance.delete()

    @action(detail=True, methods=["post"], url_path="status")
    def set_status(self, request, pk=None):
        campaign = self.get_object()
        serializer = CampaignStatusActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]
        try:
            transition_campaign(campaign, new_status)
        except DjangoValidationError as exc:
            return Response(
                {"error": {"code": "invalid_transition", "message": "; ".join(exc.messages)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        campaign.refresh_from_db()
        return Response(CampaignDetailSerializer(campaign).data)

    @action(detail=True, methods=["post"], url_path="prepare")
    def prepare(self, request, pk=None):
        """Validate and snapshot audience; move to READY."""
        campaign = self.get_object()
        try:
            count = prepare_campaign(campaign)
        except DjangoValidationError as exc:
            return Response(
                {"error": {"code": "invalid_campaign", "message": "; ".join(exc.messages)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        campaign.refresh_from_db()
        return Response(
            {
                "status": campaign.status,
                "eligible_count": count,
                "campaign": CampaignDetailSerializer(campaign).data,
                "message": (
                    f"Campaign validated and prepared with {count} eligible leads. "
                    "Note: Phase 6 does not send real e-mails."
                ),
            }
        )

    @action(detail=True, methods=["get"], url_path="preview-audience")
    def preview_audience(self, request, pk=None):
        """Return paginated eligible leads for the campaign (live query)."""
        campaign = self.get_object()
        qs = eligible_leads_qs(campaign)
        # Simple DRF pagination through the list's paginator.
        page = self.paginate_queryset(qs)
        serializer = LeadListSerializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="members")
    def members(self, request, pk=None):
        campaign = self.get_object()
        qs = (
            CampaignLead.objects.filter(campaign=campaign)
            .select_related("lead", "lead__company", "lead__contact")
            .order_by("-created_at")
        )
        send_status = request.query_params.get("send_status")
        if send_status:
            qs = qs.filter(send_status=send_status)
        page = self.paginate_queryset(qs)
        from apps.campaigns.serializers import CampaignLeadSerializer

        serializer = CampaignLeadSerializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="statuses")
    def statuses(self, request):
        counts = {
            row["status"]: row["total"]
            for row in Campaign.objects.values("status").annotate(total=Count("id"))
        }
        payload = status_vocabulary()
        for entry in payload["campaign_status"]:
            entry["count"] = counts.get(entry["value"], 0)
        payload["total"] = sum(counts.values())
        return Response(payload)

    @action(detail=True, methods=["get"], url_path="validate")
    def validate(self, request, pk=None):
        campaign = self.get_object()
        errors = validate_campaign_for_launch(campaign)
        return Response(
            {
                "valid": not errors,
                "errors": errors,
                "eligible_count": count_eligible_leads(campaign),
            }
        )
