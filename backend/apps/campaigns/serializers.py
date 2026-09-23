"""Serializers for Campaigns (Phase 6)."""

from __future__ import annotations

from rest_framework import serializers

from apps.campaigns.models import Campaign, CampaignLead, CampaignStatus
from apps.campaigns.services import (
    count_eligible_leads,
    validate_campaign_for_launch,
)
from apps.email_engine.models import EmailTemplate
from apps.email_engine.serializers import EmailTemplateSerializer


class CampaignLeadSerializer(serializers.ModelSerializer):
    lead_name = serializers.CharField(source="lead.company_name", read_only=True)
    contact_name = serializers.CharField(source="lead.contact_name", read_only=True)
    email = serializers.CharField(source="lead.email", read_only=True)

    class Meta:
        model = CampaignLead
        fields = (
            "id",
            "lead",
            "lead_name",
            "contact_name",
            "email",
            "send_status",
            "sent_at",
            "replied_at",
            "created_at",
        )
        read_only_fields = fields


class CampaignSerializer(serializers.ModelSerializer):
    template_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    eligible_count = serializers.IntegerField(read_only=True)
    audience_preview = serializers.SerializerMethodField()
    can_launch = serializers.SerializerMethodField()
    launch_errors = serializers.SerializerMethodField()
    progress_pct = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = (
            "id",
            "name",
            "description",
            "industry",
            "sub_industry",
            "location",
            "minimum_lead_score",
            "recommended_service",
            "template",
            "template_name",
            "scheduled_start_at",
            "scheduled_end_at",
            "sending_start_time",
            "sending_end_time",
            "daily_limit",
            "status",
            "status_display",
            "eligible_count",
            "sent_count",
            "reply_count",
            "meeting_count",
            "audience_preview",
            "can_launch",
            "launch_errors",
            "progress_pct",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "eligible_count",
            "sent_count",
            "reply_count",
            "meeting_count",
            "created_at",
            "updated_at",
        )

    def get_template_name(self, obj) -> str:
        return obj.template.name if obj.template_id else ""

    def get_audience_preview(self, obj) -> dict:
        return obj.audience_filters()

    def get_can_launch(self, obj) -> bool:
        return not validate_campaign_for_launch(obj)

    def get_launch_errors(self, obj) -> list[str]:
        return validate_campaign_for_launch(obj)

    def get_progress_pct(self, obj) -> int:
        if obj.eligible_count == 0:
            return 0
        sent = obj.sent_count or 0
        pct = round(sent * 100 / obj.eligible_count)
        return min(100, max(0, pct))

    def validate_template(self, value):
        if (
            value is not None
            and not EmailTemplate.objects.filter(
                pk=value.pk if hasattr(value, "pk") else value
            ).exists()
        ):
            raise serializers.ValidationError("Selected template does not exist.")
        return value

    def validate_daily_limit(self, value: int) -> int:
        if value <= 0 or value > 10_000:
            raise serializers.ValidationError("Daily limit must be between 1 and 10000.")
        return value

    def validate_minimum_lead_score(self, value: int) -> int:
        if not 0 <= value <= 100:
            raise serializers.ValidationError("Minimum lead score must be between 0 and 100.")
        return value


class CampaignListSerializer(CampaignSerializer):
    """Compact representation for list views — includes audience size estimate."""

    audience_size = serializers.SerializerMethodField()

    class Meta(CampaignSerializer.Meta):
        fields = (*CampaignSerializer.Meta.fields, "audience_size")

    def get_audience_size(self, obj) -> int:
        # Use cached eligible_count for READY+ campaigns; otherwise compute live.
        if obj.eligible_count:
            return obj.eligible_count
        return count_eligible_leads(obj)


class CampaignDetailSerializer(CampaignSerializer):
    template_detail = serializers.SerializerMethodField()
    memberships = serializers.SerializerMethodField()

    class Meta(CampaignSerializer.Meta):
        fields = (*CampaignSerializer.Meta.fields, "template_detail", "memberships")

    def get_template_detail(self, obj):
        if not obj.template_id:
            return None
        return EmailTemplateSerializer(obj.template).data

    def get_memberships(self, obj) -> int:
        return obj.memberships.count()


class CampaignWizardSerializer(serializers.Serializer):
    """Payload accepted at each wizard step. Only step 1/2/3/4/5 are explicit;
    the backend doesn't care about the step number — it always validates the
    full campaign before launch."""

    name = serializers.CharField(required=False, allow_blank=True, max_length=180)
    description = serializers.CharField(required=False, allow_blank=True)
    industry = serializers.CharField(required=False, allow_blank=True, max_length=120)
    sub_industry = serializers.CharField(required=False, allow_blank=True, max_length=120)
    location = serializers.CharField(required=False, allow_blank=True, max_length=120)
    minimum_lead_score = serializers.IntegerField(
        required=False, min_value=0, max_value=100, default=0
    )
    recommended_service = serializers.CharField(required=False, allow_blank=True, max_length=180)
    template = serializers.IntegerField(required=False, allow_null=True)
    template_data = serializers.DictField(required=False, allow_null=True)
    scheduled_start_at = serializers.DateTimeField(required=False, allow_null=True)
    scheduled_end_at = serializers.DateTimeField(required=False, allow_null=True)
    sending_start_time = serializers.TimeField(required=False, allow_null=True)
    sending_end_time = serializers.TimeField(required=False, allow_null=True)
    daily_limit = serializers.IntegerField(required=False, min_value=1, max_value=10000, default=90)


class CampaignStatusActionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=CampaignStatus.choices)


def status_vocabulary() -> dict:
    return {
        "campaign_status": [
            {"value": value, "label": label} for value, label in CampaignStatus.choices
        ],
        "default_daily_limit": 90,
    }
