"""Serializers for email templates (Phase 6)."""

from __future__ import annotations

from rest_framework import serializers

from apps.email_engine.models import EmailTemplate, SAMPLE_LEAD, TEMPLATE_VARIABLES


class EmailTemplateSerializer(serializers.ModelSerializer):
    used_variables = serializers.ListField(child=serializers.CharField(), read_only=True)
    unknown_variables = serializers.ListField(child=serializers.CharField(), read_only=True)
    missing_variables = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = EmailTemplate
        fields = (
            "id",
            "name",
            "description",
            "subject",
            "body",
            "default_recommended_service",
            "used_variables",
            "unknown_variables",
            "missing_variables",
            "created_at",
            "updated_at",
        )


class TemplatePreviewSerializer(serializers.Serializer):
    """Render a template (existing or ad-hoc) against the sample lead."""

    subject = serializers.CharField(required=False, allow_blank=True)
    body = serializers.CharField(required=False, allow_blank=True)
    context = serializers.DictField(required=False, child=serializers.CharField(), default=dict)

    def preview(self, template: EmailTemplate | None = None) -> dict:
        ctx = {**SAMPLE_LEAD, **(self.validated_data.get("context") or {})}
        if template is not None:
            return {
                "subject": template.render_preview(ctx)["subject"],
                "body": template.render_preview(ctx)["body"],
                "sample": ctx,
                "variables": template.used_variables(),
            }
        from apps.email_engine.models import render_template

        subject = self.validated_data.get("subject") or ""
        body = self.validated_data.get("body") or ""
        return {
            "subject": render_template(subject, ctx),
            "body": render_template(body, ctx),
            "sample": ctx,
        }


def template_variables() -> dict:
    return {
        "supported_variables": TEMPLATE_VARIABLES,
        "sample_lead": SAMPLE_LEAD,
    }
