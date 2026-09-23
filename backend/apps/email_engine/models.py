"""
E-mail templates and outbound delivery records.

Phase 6 added reusable templates and preview rendering. Phase 7 adds the
persisted outbound message state and the concurrency-safe daily marketing
sending ledger used by the Celery SMTP worker.
"""

from __future__ import annotations

import re
from typing import Any

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models

from core.models import TimeStampedModel

__all__ = [
    "TEMPLATE_VARIABLES",
    "DailyEmailUsage",
    "EmailMessage",
    "EmailMessageStatus",
    "EmailTemplate",
    "render_template",
]


# Variables supported by the template engine. Values must match the exact
# spelling of the keys expected by the UI so validation errors are actionable.
TEMPLATE_VARIABLES = [
    "first_name",
    "contact_name",
    "company_name",
    "industry",
    "city",
    "state",
    "website",
    "recommended_service",
]

_VAR_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")

SAMPLE_LEAD: dict[str, str] = {
    "first_name": "Alex",
    "contact_name": "Alex Morgan",
    "company_name": "Northwind Logistics, Inc.",
    "industry": "Transportation & Logistics",
    "city": "Columbus",
    "state": "OH",
    "website": "https://northwindlogistics.com",
    "recommended_service": "Freight Optimization Review",
}


class EmailTemplate(TimeStampedModel):
    """Reusable outbound e-mail template with subject + body."""

    name = models.CharField(max_length=180, validators=[MinLengthValidator(2)])
    description = models.TextField(blank=True, default="")
    subject = models.CharField(max_length=255, validators=[MinLengthValidator(3)])
    body = models.TextField(validators=[MinLengthValidator(10)])

    # Optional default for campaigns that don't override the service.
    default_recommended_service = models.CharField(max_length=180, blank=True, default="")

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def used_variables(self) -> list[str]:
        """Variables present in subject+body, in first-use order (deduped)."""
        seen: set[str] = set()
        out: list[str] = []
        for source in (self.subject, self.body):
            for match in _VAR_PATTERN.finditer(source):
                name = match.group(1)
                if name not in seen:
                    seen.add(name)
                    out.append(name)
        return out

    def unknown_variables(self) -> list[str]:
        """Variables present in the template but not in the supported list."""
        allowed = set(TEMPLATE_VARIABLES)
        return [name for name in self.used_variables() if name not in allowed]

    def missing_variables(self) -> list[str]:
        """Supported variables that the template does NOT reference (informational)."""
        used = set(self.used_variables())
        return [name for name in TEMPLATE_VARIABLES if name not in used]

    def render_preview(self, context: dict[str, Any] | None = None) -> dict[str, str]:
        """Render subject + body against a sample context (defaults to SAMPLE_LEAD)."""
        ctx = {**SAMPLE_LEAD, **(context or {})}
        return {
            "subject": render_template(self.subject, ctx),
            "body": render_template(self.body, ctx),
        }


def render_template(template: str, context: dict[str, Any]) -> str:
    """
    Replace ``{{ var }}`` placeholders with ``context[var]``.

    Unknown variables are replaced with an empty string so rendering never
    raises — editors see the hole disappear instead of crashing. Actual
    delivery still uses the exact same renderer and stores the rendered
    subject/body snapshot on EmailMessage.
    """

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        value = context.get(name, "")
        return "" if value is None else str(value)

    return _VAR_PATTERN.sub(replace, template)


class EmailMessageStatus(models.TextChoices):
    QUEUED = "QUEUED", "Queued"
    PROCESSING = "PROCESSING", "Processing"
    SENT = "SENT", "Sent"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"
    BOUNCED = "BOUNCED", "Bounced"


class EmailMessage(TimeStampedModel):
    """One idempotent outbound message for one campaign lead."""

    campaign = models.ForeignKey(
        "campaigns.Campaign",
        on_delete=models.CASCADE,
        related_name="email_messages",
    )
    lead = models.ForeignKey(
        "leads.Lead",
        on_delete=models.CASCADE,
        related_name="email_messages",
    )
    to_email = models.EmailField(max_length=320)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=EmailMessageStatus.choices,
        default=EmailMessageStatus.QUEUED,
        db_index=True,
    )
    scheduled_at = models.DateTimeField(db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")
    attempt_count = models.PositiveIntegerField(default=0)

    # A reservation belongs to a particular calendar day. Keeping it on the
    # message makes a retry idempotent: the same message never reserves a
    # second slot on the same day, while a retry after midnight is counted in
    # the new day's limit too.
    daily_slot_reserved = models.BooleanField(default=False, editable=False)
    daily_slot_date = models.DateField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ("scheduled_at", "id")
        constraints = (
            models.UniqueConstraint(
                fields=["campaign", "lead"],
                name="email_message_one_per_campaign_lead",
            ),
        )
        indexes = (
            models.Index(fields=["status", "scheduled_at"], name="email_msg_status_sched_idx"),
            models.Index(fields=["campaign", "status"], name="email_msg_campaign_status_idx"),
        )

    def __str__(self) -> str:
        return f"Email #{self.pk} to {self.to_email} ({self.status})"


class DailyEmailUsage(TimeStampedModel):
    """Atomic per-day reservation ledger for marketing e-mails."""

    date = models.DateField(unique=True, db_index=True)
    sent_count = models.PositiveIntegerField(default=0)
    limit = models.PositiveIntegerField(default=90)

    class Meta:
        ordering = ("-date",)

    def __str__(self) -> str:
        return f"{self.date}: {self.sent_count}/{self.limit}"

    @classmethod
    def configured_limit(cls) -> int:
        return int(getattr(settings, "OUTREACH_DAILY_EMAIL_LIMIT", 90))
