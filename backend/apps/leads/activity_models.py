"""
Lead activity, notes, and tags (Phase 5).

Three small models support the lead detail page:

* ``LeadNote`` — free-text notes attached to a lead (simple chronological feed).
* ``LeadActivity`` — immutable events (status change, score change, note added,
  email sent, merge, import, campaign step, etc.). The UI renders an icon and
  label per event type.
* ``LeadTag`` (optional in Phase 5) not added yet — bulk suppression uses
  email_status changes, which already feed into the activity log.

Both models are append-only; nothing is ever deleted.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.leads.models import Lead
from core.models import TimeStampedModel

__all__ = ["LeadNote", "LeadActivity", "ActivityType"]


class ActivityType(models.TextChoices):
    CREATED = "CREATED", _("Created")
    IMPORTED = "IMPORTED", _("Imported")
    STATUS_CHANGE = "STATUS_CHANGE", _("Status change")
    SCORE_CHANGE = "SCORE_CHANGE", _("Score change")
    NOTE_ADDED = "NOTE_ADDED", _("Note added")
    EMAIL_SENT = "EMAIL_SENT", _("E-mail sent")
    EMAIL_OPENED = "EMAIL_OPENED", _("E-mail opened")
    REPLY = "REPLY", _("Reply")
    MEETING = "MEETING", _("Meeting booked")
    MERGED = "MERGED", _("Merged")
    SUPPRESSED = "SUPPRESSED", _("Suppressed")
    BULK_EDIT = "BULK_EDIT", _("Bulk edit")
    CAMPAIGN_ADDED = "CAMPAIGN_ADDED", _("Added to campaign")
    EXPORTED = "EXPORTED", _("Exported")
    NOTE = "NOTE", _("Note")
    MANUAL_EDIT = "MANUAL_EDIT", _("Manual edit")


class LeadActivity(TimeStampedModel):
    """An immutable event in the lead's timeline."""

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="activities",
        verbose_name=_("lead"),
    )
    activity_type = models.CharField(
        _("type"), max_length=24, choices=ActivityType.choices, db_index=True
    )
    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    # Optional structured payload (e.g. {"old_status": "NEW", "new_status": "QUALIFIED"}).
    metadata = models.JSONField(_("metadata"), default=dict, blank=True)
    actor = models.CharField(_("actor"), max_length=120, blank=True)

    class Meta:
        verbose_name = _("lead activity")
        verbose_name_plural = _("lead activities")
        ordering = ("-created_at", "-id")
        indexes = (models.Index(fields=["lead", "-created_at"], name="lead_activity_lead_created_idx"),)

    def __str__(self) -> str:
        return f"{self.get_activity_type_display()} — {self.title}"


class LeadNote(TimeStampedModel):
    """A free-text note on a lead. Also creates an activity entry."""

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="notes",
        verbose_name=_("lead"),
    )
    body = models.TextField(_("body"))
    author = models.CharField(_("author"), max_length=120, blank=True)
    pinned = models.BooleanField(_("pinned"), default=False, db_index=True)

    class Meta:
        verbose_name = _("lead note")
        verbose_name_plural = _("lead notes")
        ordering = ("-created_at", "-id")
        indexes = (models.Index(fields=["lead", "-created_at"], name="lead_note_lead_created_idx"),)

    def __str__(self) -> str:
        return f"Note on Lead #{self.lead_id} at {self.created_at:%Y-%m-%d %H:%M}"
