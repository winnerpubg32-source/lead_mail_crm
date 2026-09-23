"""Serializers for the leads module (Phase 5: detail + notes + scoring)."""

from __future__ import annotations

from rest_framework import serializers

from apps.leads.activity_models import ActivityType, LeadActivity, LeadNote
from apps.leads.models import EmailStatus, Lead, LeadStatus
from apps.leads.scoring import ScoreClassification, classify_score, compute_lead_score


class LeadStatusSerializer(serializers.Serializer):
    """Choice metadata so the frontend renders labels from one source."""

    value = serializers.CharField()
    label = serializers.CharField()


class ScoreBreakdownSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    classification = serializers.ChoiceField(choices=ScoreClassification.choices)
    label = serializers.CharField()
    components = serializers.DictField(child=serializers.IntegerField())


class LeadNoteSerializer(serializers.ModelSerializer):
    author_display = serializers.SerializerMethodField()

    class Meta:
        model = LeadNote
        fields = ("id", "body", "author", "author_display", "pinned", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def get_author_display(self, obj) -> str:
        return obj.author or "System"

    def create(self, validated_data):
        request = self.context.get("request")
        if request and not validated_data.get("author") and hasattr(request, "user"):
            user = request.user
            if user and user.is_authenticated:
                validated_data["author"] = user.email or str(user)
        return super().create(validated_data)


class LeadActivitySerializer(serializers.ModelSerializer):
    type_label = serializers.CharField(source="get_activity_type_display", read_only=True)

    class Meta:
        model = LeadActivity
        fields = (
            "id",
            "activity_type",
            "type_label",
            "title",
            "description",
            "metadata",
            "actor",
            "created_at",
        )
        read_only_fields = fields


class LeadSerializer(serializers.ModelSerializer):
    """Full lead representation."""

    company_name = serializers.CharField(read_only=True)
    contact_name = serializers.CharField(read_only=True)
    job_title = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True)
    website = serializers.CharField(source="company.website", read_only=True)
    website_domain = serializers.CharField(source="company.normalized_website", read_only=True)
    street_address = serializers.CharField(source="company.street_address", read_only=True)
    zip_code = serializers.CharField(source="company.zip_code", read_only=True)
    country = serializers.CharField(source="company.country", read_only=True)
    sub_industry = serializers.CharField(source="company.sub_industry", read_only=True)
    last_contact = serializers.SerializerMethodField()
    industry = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    state = serializers.CharField(read_only=True)
    is_contactable = serializers.BooleanField(read_only=True)
    lead_status_display = serializers.CharField(source="get_lead_status_display", read_only=True)
    email_status_display = serializers.CharField(source="get_email_status_display", read_only=True)
    # "CRM Status" in the brief is the pipeline state (lead_status).
    crm_status = serializers.CharField(source="lead_status", read_only=True)
    crm_status_display = serializers.CharField(source="get_lead_status_display", read_only=True)
    score_classification = serializers.SerializerMethodField()
    score_classification_label = serializers.SerializerMethodField()
    # Last outbound activity timestamp (email sent / meeting / reply)
    note_count = serializers.SerializerMethodField()
    activity_count = serializers.SerializerMethodField()

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
            "website",
            "website_domain",
            "street_address",
            "city",
            "state",
            "zip_code",
            "country",
            "industry",
            "sub_industry",
            "lead_score",
            "score_classification",
            "score_classification_label",
            "lead_status",
            "lead_status_display",
            "crm_status",
            "crm_status_display",
            "email_status",
            "email_status_display",
            "source",
            "source_file",
            "source_row_number",
            "last_contact",
            "note_count",
            "activity_count",
            "is_contactable",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "crm_status")

    def get_score_classification(self, obj) -> str:
        return classify_score(obj.lead_score, obj.email_status)

    def get_score_classification_label(self, obj) -> str:
        code = self.get_score_classification(obj)
        return dict(ScoreClassification.choices).get(code, code)

    def get_note_count(self, obj) -> int:
        return getattr(obj, "note_count", None) or 0

    def get_activity_count(self, obj) -> int:
        return getattr(obj, "activity_count", None) or 0

    def get_last_contact(self, obj):
        # Prefer an annotated value; fall back to None if not loaded.
        last = getattr(obj, "last_contact_at", None)
        return last


class LeadListSerializer(LeadSerializer):
    class Meta(LeadSerializer.Meta):
        pass


class LeadDetailSerializer(LeadSerializer):
    """Detail payload includes notes + activity timeline."""

    notes = LeadNoteSerializer(many=True, read_only=True)
    activities = LeadActivitySerializer(many=True, read_only=True)
    score_breakdown = serializers.SerializerMethodField()

    class Meta(LeadSerializer.Meta):
        fields = LeadSerializer.Meta.fields + ("notes", "activities", "score_breakdown")

    def get_score_breakdown(self, obj) -> dict:
        score, components = compute_lead_score(obj)
        code = classify_score(score, obj.email_status)
        return {
            "total": score,
            "classification": code,
            "label": dict(ScoreClassification.choices).get(code, code),
            "components": components.as_dict(),
        }


class LeadUpdateSerializer(serializers.ModelSerializer):
    """Write-serializer for PATCH /leads/{id}/ (detail edits)."""

    class Meta:
        model = Lead
        fields = ("lead_status", "email_status", "lead_score", "source")

    def validate_lead_score(self, value: int) -> int:
        if not 0 <= value <= 100:
            raise serializers.ValidationError("Lead score must be between 0 and 100.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs.get("lead_status") == LeadStatus.DO_NOT_CONTACT:
            attrs["email_status"] = EmailStatus.SUPPRESSED
        return attrs


class LeadNoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadNote
        fields = ("id", "body", "pinned", "created_at")
        read_only_fields = ("id", "created_at")


class BulkActionSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False, max_length=1000)
    action = serializers.ChoiceField(
        choices=[
            ("change_status", "change_status"),
            ("change_industry", "change_industry"),
            ("assign_campaign", "assign_campaign"),
            ("suppress", "suppress"),
            ("export", "export"),
        ]
    )
    lead_status = serializers.ChoiceField(choices=LeadStatus.choices, required=False)
    email_status = serializers.ChoiceField(choices=EmailStatus.choices, required=False)
    industry = serializers.CharField(required=False, allow_blank=True)
    campaign_name = serializers.CharField(required=False, allow_blank=True)


def status_choices() -> dict[str, list[dict[str, str]]]:
    """Enum vocabulary for the dashboard filters."""
    return {
        "lead_status": [{"value": value, "label": label} for value, label in LeadStatus.choices],
        "email_status": [{"value": value, "label": label} for value, label in EmailStatus.choices],
        "score_classification": [
            {"value": value, "label": label} for value, label in ScoreClassification.choices
        ],
    }
