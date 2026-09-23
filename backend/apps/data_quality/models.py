"""
Data-quality models (Phase 4).

Three small tables support the duplicate review workflow:

* ``DuplicateGroup``  — a cluster of two or more leads/companies/contacts the
  detector believes may be the same record. A confidence score, the detection
  reason, and a status (open/merged/kept/ignored) drive the UI.
* ``DuplicateGroupMember`` — one lead inside a duplicate group. Each group
  references exactly two records for the pairwise comparison view (we can
  always split larger clusters into pairs).
* ``MergeAudit`` — a permanent log of every merge, including which records
  were combined, which record survived, and which fields were taken from the
  loser. Provenance (source_file/source_row_number) is never deleted: the
  loser lead is kept as a soft-redirector with status=MERGED.
"""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel

__all__ = [
    "DuplicateGroup",
    "DuplicateGroupMember",
    "MergeAudit",
    "DuplicateStatus",
    "MATCH_REASON_CHOICES",
]


class DuplicateStatus(models.TextChoices):
    """Workflow state of a detected duplicate pair."""

    OPEN = "OPEN", _("Open")
    MERGED = "MERGED", _("Merged")
    KEPT_BOTH = "KEPT_BOTH", _("Kept both")
    IGNORED = "IGNORED", _("Ignored")


#: Detection reasons ordered from highest confidence to lowest. The human
#: readable label is shown on the review card; the code is used by the service
#: to decide confidence.
MATCH_REASON_CHOICES = (
    ("EMAIL", _("Same normalized e-mail")),
    ("COMPANY_WEBSITE", _("Same company + website")),
    ("COMPANY_PHONE", _("Same company + phone")),
    ("COMPANY_ADDRESS", _("Same company + address")),
    ("COMPANY_CITY_STATE", _("Same company + city + state")),
    ("CONTACT_NAME_COMPANY", _("Same contact name + company")),
)

#: Weight assigned to each reason; used both at detection time and in the UI.
MATCH_CONFIDENCE = {
    "EMAIL": 100,
    "COMPANY_WEBSITE": 95,
    "COMPANY_PHONE": 90,
    "COMPANY_ADDRESS": 80,
    "CONTACT_NAME_COMPANY": 70,
    "COMPANY_CITY_STATE": 60,
}


class DuplicateGroup(TimeStampedModel):
    """
    A pair of records flagged as potential duplicates.

    We model "pairs" instead of arbitrary-sized clusters because the review
    workflow is inherently pairwise: the reviewer is shown Record A vs Record B
    and picks an action. Larger clusters are represented as multiple groups
    sharing a ``cluster_key`` so the UI can present them together if it wants.
    """

    reason_code = models.CharField(_("reason code"), max_length=32, choices=MATCH_REASON_CHOICES)
    confidence = models.PositiveSmallIntegerField(_("confidence"), db_index=True)
    status = models.CharField(
        _("status"),
        max_length=16,
        choices=DuplicateStatus.choices,
        default=DuplicateStatus.OPEN,
        db_index=True,
    )
    # Shared identifier when a detector produces more than two overlapping
    # matches (e.g. three rows with the same e-mail). Groups without a cluster
    # leave this blank.
    cluster_key = models.CharField(_("cluster key"), max_length=255, blank=True, db_index=True)

    # Result of a merge (populated when status=MERGED).
    surviving_lead = models.ForeignKey(
        "leads.Lead",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("surviving lead"),
    )
    resolved_by = models.CharField(_("resolved by"), max_length=120, blank=True)
    resolved_at = models.DateTimeField(_("resolved at"), null=True, blank=True)

    class Meta:
        verbose_name = _("duplicate group")
        verbose_name_plural = _("duplicate groups")
        ordering = ("-confidence", "-created_at")
        indexes = (
            models.Index(fields=["status", "-confidence"], name="dq_status_conf_idx"),
            models.Index(fields=["reason_code", "status"], name="dq_reason_status_idx"),
        )

    def __str__(self) -> str:
        return f"Duplicate #{self.pk} ({self.reason_code}, {self.confidence}%)"


class DuplicateGroupMember(TimeStampedModel):
    """One lead flagged as part of a duplicate group."""

    group = models.ForeignKey(
        DuplicateGroup,
        on_delete=models.CASCADE,
        related_name="members",
        verbose_name=_("group"),
    )
    lead = models.ForeignKey(
        "leads.Lead",
        on_delete=models.CASCADE,
        related_name="duplicate_memberships",
        verbose_name=_("lead"),
    )
    role = models.CharField(
        _("role"),
        max_length=10,
        choices=(("A", "A"), ("B", "B")),
        default="A",
    )

    class Meta:
        verbose_name = _("duplicate group member")
        verbose_name_plural = _("duplicate group members")
        ordering = ("role", "id")
        constraints = (
            models.UniqueConstraint(
                fields=["group", "lead"],
                name="dq_member_unique_per_group",
            ),
        )

    def __str__(self) -> str:
        return f"Lead #{self.lead_id} in group #{self.group_id}"


class MergeAudit(TimeStampedModel):
    """
    Immutable audit row for every merge performed through the review UI.

    Provenance is preserved on the surviving lead; a MergeAudit entry explains
    why the losing lead disappeared and which fields were brought over from it.
    The loser lead itself is kept (status=MERGED, ``merged_into`` points to the
    winner), so source/source_file/source_row_number survive even if the review
    is later undone.
    """

    surviving_lead = models.ForeignKey(
        "leads.Lead",
        on_delete=models.CASCADE,
        related_name="merge_winners",
        verbose_name=_("surviving lead"),
    )
    merged_lead = models.ForeignKey(
        "leads.Lead",
        on_delete=models.CASCADE,
        related_name="merge_losers",
        verbose_name=_("merged lead"),
    )
    duplicate_group = models.ForeignKey(
        DuplicateGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="merges",
        verbose_name=_("duplicate group"),
    )
    reason_code = models.CharField(_("reason code"), max_length=32, choices=MATCH_REASON_CHOICES)
    confidence = models.PositiveSmallIntegerField(_("confidence"))
    fields_from_merged = models.JSONField(
        _("fields taken from the merged record"), default=dict, blank=True
    )
    merged_sources = models.JSONField(
        _("preserved source list"), default=list, blank=True
    )
    performed_by = models.CharField(_("performed by"), max_length=120, blank=True)

    class Meta:
        verbose_name = _("merge audit")
        verbose_name_plural = _("merge audits")
        ordering = ("-created_at",)
        indexes = (
            models.Index(fields=["surviving_lead"], name="dq_merge_winner_idx"),
            models.Index(fields=["merged_lead"], name="dq_merge_loser_idx"),
        )

    def __str__(self) -> str:
        return f"Merge #{self.pk}: lead {self.merged_lead_id} -> {self.surviving_lead_id}"
