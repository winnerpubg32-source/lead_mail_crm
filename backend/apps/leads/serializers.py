"""Serializers for the leads module."""

from __future__ import annotations

from rest_framework import serializers

from apps.leads.models import EmailStatus, Lead, LeadStatus


class LeadStatusSerializer(serializers.Serializer):
    """Choice metadata so the frontend renders labels from one source."""

    value = serializers.CharField()
    label = serializers.CharField()


class LeadSerializer(serializers.ModelSerializer):
    """Full lead representation."""

    company_name = serializers.CharField(read_only=True)
    contact_name = serializers.CharField(read_only=True)
    job_title = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True)
    industry = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    state = serializers.CharField(read_only=True)
    is_contactable = serializers.BooleanField(read_only=True)
    lead_status_display = serializers.CharField(source="get_lead_status_display", read_only=True)
    email_status_display = serializers.CharField(source="get_email_status_display", read_only=True)

    class Meta:
        model = Lead
        fields = (
            "id",
            "company",
            "company_name",
            "contact",
            "contact_name",
            "job_title",
            "email",
            "phone",
            "industry",
            "city",
            "state",
            "lead_score",
            "lead_status",
            "lead_status_display",
            "email_status",
            "email_status_display",
            "source",
            "source_file",
            "source_row_number",
            "is_contactable",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class LeadListSerializer(LeadSerializer):
    """List payload — identical columns to the detail view for now."""

    class Meta(LeadSerializer.Meta):
        fields = LeadSerializer.Meta.fields


class LeadWriteSerializer(serializers.ModelSerializer):
    """
    Validation entry point for the (future) import and manual-edit paths.

    Not exposed by a route yet — Phase 2 is read-only — but keeping it here
    documents the accepted payload and is used by the API tests.
    """

    class Meta:
        model = Lead
        fields = (
            "company",
            "contact",
            "lead_score",
            "lead_status",
            "email_status",
            "source",
            "source_file",
            "source_row_number",
        )

    def validate_lead_score(self, value: int) -> int:
        if not 0 <= value <= 100:
            raise serializers.ValidationError("Lead score must be between 0 and 100.")
        return value

    def validate(self, attrs: dict) -> dict:
        contact = attrs.get("contact")
        company = attrs.get("company")
        if contact and company and contact.company_id and contact.company_id != company.id:
            raise serializers.ValidationError(
                {"contact": "The selected contact belongs to a different company."}
            )
        if attrs.get("lead_status") == LeadStatus.DO_NOT_CONTACT:
            attrs["email_status"] = EmailStatus.SUPPRESSED
        return attrs


def status_choices() -> dict[str, list[dict[str, str]]]:
    """Enum vocabulary for the dashboard filters."""
    return {
        "lead_status": [{"value": value, "label": label} for value, label in LeadStatus.choices],
        "email_status": [{"value": value, "label": label} for value, label in EmailStatus.choices],
    }
