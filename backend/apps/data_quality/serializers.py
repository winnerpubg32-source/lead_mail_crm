"""Serializers for the data-quality API (Phase 4)."""

from __future__ import annotations

from rest_framework import serializers

from apps.data_quality.models import (
    MATCH_CONFIDENCE,
    DuplicateGroup,
    DuplicateGroupMember,
    DuplicateStatus,
    MergeAudit,
)
from apps.leads.models import Lead
from apps.leads.serializers import LeadSerializer


class DataQualityStatsSerializer(serializers.Serializer):
    """Payload for the dashboard card."""

    total_leads = serializers.IntegerField()
    valid_emails = serializers.IntegerField()
    invalid_emails = serializers.IntegerField()
    missing_emails = serializers.IntegerField()
    missing_phones = serializers.IntegerField()
    missing_websites = serializers.IntegerField()
    duplicate_groups = serializers.IntegerField()
    missing_contact_names = serializers.IntegerField()


class DuplicateGroupMemberSerializer(serializers.ModelSerializer):
    lead = LeadSerializer(read_only=True)

    class Meta:
        model = DuplicateGroupMember
        fields = ("id", "role", "lead")


class DuplicateGroupSerializer(serializers.ModelSerializer):
    reason_label = serializers.CharField(source="get_reason_code_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    members = DuplicateGroupMemberSerializer(many=True, read_only=True)
    record_a = serializers.SerializerMethodField()
    record_b = serializers.SerializerMethodField()

    class Meta:
        model = DuplicateGroup
        fields = (
            "id",
            "reason_code",
            "reason_label",
            "confidence",
            "status",
            "status_label",
            "cluster_key",
            "members",
            "record_a",
            "record_b",
            "created_at",
            "updated_at",
        )

    def get_record_a(self, obj) -> dict | None:
        return self._record_for_role(obj, "A")

    def get_record_b(self, obj) -> dict | None:
        return self._record_for_role(obj, "B")

    def _record_for_role(self, obj, role: str) -> dict | None:
        member = next((m for m in obj.members.all() if m.role == role), None)
        if not member:
            return None
        return LeadSerializer(member.lead).data


class MergeRequestSerializer(serializers.Serializer):
    """Input for the ``merge`` action."""

    winner = serializers.IntegerField()
    loser = serializers.IntegerField()

    def validate(self, attrs: dict) -> dict:
        if attrs["winner"] == attrs["loser"]:
            raise serializers.ValidationError("Winner and loser must be different leads.")
        return attrs


class MergeAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = MergeAudit
        fields = (
            "id",
            "surviving_lead",
            "merged_lead",
            "reason_code",
            "confidence",
            "fields_from_merged",
            "merged_sources",
            "performed_by",
            "created_at",
        )


class ResolveRequestSerializer(serializers.Serializer):
    """Input for ignore / keep-both actions."""

    performed_by = serializers.CharField(required=False, allow_blank=True, default="")


class MissingEmailLeadSerializer(LeadSerializer):
    """Same shape as a lead, used by the missing-email list."""

    website = serializers.CharField(source="company.website", read_only=True)
    country = serializers.CharField(source="company.country", read_only=True)

    class Meta(LeadSerializer.Meta):
        fields = LeadSerializer.Meta.fields + ("website", "country")
