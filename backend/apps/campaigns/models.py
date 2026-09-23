"""
Campaign models (Phase 6).

A Campaign describes an outreach sequence: audience targeting rules, an
e-mail template, a daily send limit, and a lifecycle status. Phase 6
validates and prepares campaigns but does NOT send real e-mails (that
ships in Phase 7).
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from core.models import TimeStampedModel

__all__ = ["Campaign", "CampaignStatus", "CampaignLead"]


class CampaignStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    READY = "READY", "Ready"
    RUNNING = "RUNNING", "Running"
    PAUSED = "PAUSED", "Paused"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


# Allowed transitions so accidental cross-state jumps are blocked.
STATUS_TRANSITIONS: dict[str, set[str]] = {
    CampaignStatus.DRAFT: {CampaignStatus.READY, CampaignStatus.CANCELLED},
    CampaignStatus.READY: {CampaignStatus.RUNNING, CampaignStatus.DRAFT, CampaignStatus.CANCELLED},
    CampaignStatus.RUNNING: {CampaignStatus.PAUSED, CampaignStatus.COMPLETED, CampaignStatus.CANCELLED},
    CampaignStatus.PAUSED: {CampaignStatus.RUNNING, CampaignStatus.CANCELLED},
    CampaignStatus.COMPLETED: set(),
    CampaignStatus.CANCELLED: set(),
}


class Campaign(TimeStampedModel):
    """An outreach campaign with audience targeting + scheduling."""

    name = models.CharField(max_length=180)
    description = models.TextField(blank=True, default="")

    # Audience filters (all optional; ANDed together when present).
    industry = models.CharField(max_length=120, blank=True, default="")
    sub_industry = models.CharField(max_length=120, blank=True, default="")
    location = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Free-text location filter (city/state or region).",
    )
    minimum_lead_score = models.PositiveSmallIntegerField(default=0)

    # Template FK (phase 6: optional so the wizard can save drafts).
    template = models.ForeignKey(
        "email_engine.EmailTemplate",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="campaigns",
    )

    # Schedule (phase 6 only stores the intended start/end; no execution yet).
    scheduled_start_at = models.DateTimeField(null=True, blank=True)
    scheduled_end_at = models.DateTimeField(null=True, blank=True)

    # Delivery cap (phase 7 enforces this against SMTP).
    daily_limit = models.PositiveIntegerField(default=90)

    # Lifecycle.
    status = models.CharField(
        max_length=20,
        choices=CampaignStatus.choices,
        default=CampaignStatus.DRAFT,
        db_index=True,
    )

    # Service recommended (Phase 6 step 2 placeholder, stored as text).
    recommended_service = models.CharField(max_length=180, blank=True, default="")

    # Counters — updated by Phase 7 when sends actually occur. Phase 6 initializes them at 0
    # so the UI always has numbers to show.
    sent_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)
    meeting_count = models.PositiveIntegerField(default=0)

    # Store eligible lead count at launch time for quick UI display.
    eligible_count = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self) -> str:
        return self.name or f"Campaign #{self.pk}"

    # -- helpers -----------------------------------------------------------
    def can_transition_to(self, new_status: str) -> bool:
        return new_status in STATUS_TRANSITIONS.get(self.status, set())

    def transition_to(self, new_status: str, *, actor: str = "") -> None:
        if not self.can_transition_to(new_status):
            raise ValidationError(
                f"Cannot transition campaign from {self.status} to {new_status}."
            )
        self.status = new_status

    def audience_filters(self) -> dict:
        """Return non-empty audience filters as a dict (used for display + queries)."""
        filters: dict[str, str | int] = {}
        if self.industry:
            filters["industry"] = self.industry
        if self.sub_industry:
            filters["sub_industry"] = self.sub_industry
        if self.location:
            filters["location"] = self.location
        if self.minimum_lead_score:
            filters["minimum_lead_score"] = self.minimum_lead_score
        return filters

    def matches_lead(self, lead) -> bool:
        """Return True if a lead instance satisfies this campaign's audience rules."""
        from apps.leads.models import EmailStatus, LeadStatus

        if lead.lead_status == LeadStatus.MERGED:
            return False
        if lead.email_status in {
            EmailStatus.INVALID,
            EmailStatus.BOUNCED,
            EmailStatus.UNSUBSCRIBED,
            EmailStatus.SUPPRESSED,
        }:
            return False
        if not lead.email:
            return False
        if lead.lead_score < (self.minimum_lead_score or 0):
            return False
        if self.industry and (lead.industry or "").lower() != self.industry.lower():
            return False
        sub = ""
        if lead.company_id:
            sub = lead.company.sub_industry or ""
        if self.sub_industry and self.sub_industry.lower() not in sub.lower():
            return False
        if self.location:
            loc = self.location.lower()
            city = lead.city or ""
            state = lead.state or ""
            country = lead.company.country if lead.company_id else ""
            haystack = " ".join(filter(None, [city, state, country])).lower()
            if loc not in haystack:
                return False
        return True


class CampaignLead(TimeStampedModel):
    """
    Join table linking leads to campaigns.

    Phase 6 populates this when a campaign moves to READY so Phase 7 has a
    fixed audience to process. Re-adding leads that are already on another
    active campaign is prevented at the service layer.
    """

    class SendStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        QUEUED = "QUEUED", "Queued"
        SENT = "SENT", "Sent"
        REPLIED = "REPLIED", "Replied"
        BOUNCED = "BOUNCED", "Bounced"
        SKIPPED = "SKIPPED", "Skipped"

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="memberships")
    lead = models.ForeignKey("leads.Lead", on_delete=models.CASCADE, related_name="campaign_memberships")
    send_status = models.CharField(
        max_length=20, choices=SendStatus.choices, default=SendStatus.PENDING, db_index=True
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("campaign", "lead")
        indexes = [
            models.Index(fields=["campaign", "send_status"]),
        ]

    def __str__(self) -> str:
        return f"{self.campaign_id} / lead {self.lead_id} ({self.send_status})"
