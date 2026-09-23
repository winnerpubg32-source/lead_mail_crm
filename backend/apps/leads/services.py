"""Lead services (Phase 5).

Helpers for:

* annotating list querysets with ``last_contact_at`` / ``note_count`` /
  ``activity_count`` so the table can render Last Contact without N+1 queries.
* recording activity events (status changes, score changes, bulk edits, notes).
* bulk update actions used by the bulk toolbar.
* CSV export of the currently filtered queryset.
"""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from typing import Iterable

from django.db import transaction
from django.db.models import Count, Max, OuterRef, Subquery
from django.http import HttpResponse
from django.utils import timezone

from apps.leads.activity_models import ActivityType, LeadActivity, LeadNote
from apps.leads.models import EmailStatus, Lead, LeadStatus
from apps.leads.scoring import compute_lead_score, rescore_leads

__all__ = [
    "annotate_lead_list",
    "record_activity",
    "record_bulk_action",
    "apply_bulk_action",
    "export_leads_csv",
    "log_creation",
]


def annotate_lead_list(queryset):
    """Add annotations for Last Contact / counts so the table stays O(1) queries."""
    last_activity = (
        LeadActivity.objects.filter(lead=OuterRef("pk"))
        .filter(
            activity_type__in=[
                ActivityType.EMAIL_SENT,
                ActivityType.EMAIL_OPENED,
                ActivityType.REPLY,
                ActivityType.MEETING,
                ActivityType.NOTE_ADDED,
                ActivityType.MANUAL_EDIT,
                ActivityType.BULK_EDIT,
                ActivityType.STATUS_CHANGE,
                ActivityType.CAMPAIGN_ADDED,
                ActivityType.SUPPRESSED,
                ActivityType.MERGED,
            ]
        )
        .order_by("-created_at")
        .values("created_at")[:1]
    )
    # NOTE: we don't want a NULL for leads with zero activity; Coalesce to updated_at
    # so the table always has something to show.
    from django.db.models.functions import Coalesce

    return queryset.annotate(
        last_contact_at=Coalesce(
            Subquery(last_activity),
            "updated_at",
        ),
        note_count=Count("notes", distinct=True),
        activity_count=Count("activities", distinct=True),
    )


def record_activity(
    lead: Lead,
    activity_type: str,
    title: str,
    description: str = "",
    metadata: dict | None = None,
    actor: str = "",
) -> LeadActivity:
    """Append a single activity entry to a lead's timeline."""
    return LeadActivity.objects.create(
        lead=lead,
        activity_type=activity_type,
        title=title,
        description=description,
        metadata=metadata or {},
        actor=actor,
    )


def log_creation(lead: Lead, *, actor: str = "system") -> None:
    """Called when a lead is first created (e.g. via import or manual entry)."""
    record_activity(
        lead,
        ActivityType.CREATED,
        title="Lead created",
        description=f"Source: {lead.source or 'manual entry'}",
        metadata={"source": lead.source, "source_file": lead.source_file},
        actor=actor,
    )


def record_note(note: LeadNote, *, actor: str = "") -> None:
    record_activity(
        note.lead,
        ActivityType.NOTE_ADDED,
        title="Note added",
        description=note.body[:120],
        actor=actor or note.author or "",
    )


def record_bulk_action(leads: Iterable[Lead], action: str, metadata: dict, *, actor: str = "system") -> None:
    for lead in leads:
        record_activity(
            lead,
            ActivityType.BULK_EDIT,
            title=f"Bulk action: {action}",
            metadata=metadata,
            actor=actor,
        )


@transaction.atomic
def apply_bulk_action(ids: list[int], action: str, **params) -> dict:
    """
    Execute a bulk action against the selected leads. Returns a summary dict.

    Supported actions:

    * ``change_status``   → set lead_status, log activity
    * ``change_industry`` → update company.industry, rescore
    * ``assign_campaign`` → log a CAMPAIGN_ADDED activity (no campaign model yet)
    * ``suppress``        → set DO_NOT_CONTACT + SUPPRESSED, rescore
    * ``export``          → no change; caller renders the CSV
    """
    leads = list(Lead.objects.select_for_update().select_related("company", "contact").filter(pk__in=ids))
    summary = {"action": action, "affected": len(leads), "ids": [l.pk for l in leads]}

    if action == "change_status":
        new_status = params["lead_status"]
        now = datetime.now(tz=UTC)
        for lead in leads:
            old_status = lead.lead_status
            lead.lead_status = new_status
            if new_status == LeadStatus.DO_NOT_CONTACT:
                lead.email_status = EmailStatus.SUPPRESSED
            lead.save(update_fields=["lead_status", "email_status", "updated_at"])
            score, _ = compute_lead_score(lead)
            lead.lead_score = score
            lead.save(update_fields=["lead_score"])
            record_activity(
                lead,
                ActivityType.STATUS_CHANGE,
                title=f"Status changed to {lead.get_lead_status_display()}",
                metadata={"old_status": old_status, "new_status": new_status, "bulk": True},
            )

    elif action == "change_industry":
        industry = params.get("industry", "")
        for lead in leads:
            if lead.company_id:
                lead.company.industry = industry
                lead.company.save(update_fields=["industry"])
            score, _ = compute_lead_score(lead)
            lead.lead_score = score
            lead.save(update_fields=["lead_score", "updated_at"])
            record_activity(
                lead,
                ActivityType.MANUAL_EDIT,
                title="Industry updated",
                metadata={"industry": industry, "bulk": True},
            )

    elif action == "assign_campaign":
        campaign_name = params.get("campaign_name") or "(unspecified)"
        for lead in leads:
            record_activity(
                lead,
                ActivityType.CAMPAIGN_ADDED,
                title=f"Added to campaign: {campaign_name}",
                metadata={"campaign_name": campaign_name, "bulk": True},
            )

    elif action == "suppress":
        for lead in leads:
            lead.lead_status = LeadStatus.DO_NOT_CONTACT
            lead.email_status = EmailStatus.SUPPRESSED
            lead.lead_score = 0
            lead.save(update_fields=["lead_status", "email_status", "lead_score", "updated_at"])
            record_activity(
                lead,
                ActivityType.SUPPRESSED,
                title="Lead suppressed",
                metadata={"bulk": True},
            )

    elif action == "export":
        for lead in leads:
            record_activity(
                lead,
                ActivityType.EXPORTED,
                title="Lead exported",
                metadata={"bulk": True},
            )

    else:
        raise ValueError(f"Unknown bulk action: {action}")

    # Rescore any leads not already scored above.
    rescore_leads([l.pk for l in leads])
    return summary


def export_leads_csv(queryset) -> HttpResponse:
    """Render the currently-filtered leads queryset as a CSV download."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "company",
            "contact",
            "job_title",
            "email",
            "phone",
            "website",
            "industry",
            "sub_industry",
            "city",
            "state",
            "country",
            "lead_score",
            "lead_status",
            "email_status",
            "source",
            "source_file",
            "source_row_number",
            "created_at",
        ]
    )
    for lead in queryset.select_related("company", "contact").iterator(chunk_size=500):
        writer.writerow(
            [
                lead.pk,
                lead.company_name,
                lead.contact_name,
                lead.job_title,
                lead.email,
                lead.phone,
                lead.company.website if lead.company_id else "",
                lead.industry,
                lead.company.sub_industry if lead.company_id else "",
                lead.city,
                lead.state,
                lead.company.country if lead.company_id else "",
                lead.lead_score,
                lead.lead_status,
                lead.email_status,
                lead.source,
                lead.source_file,
                lead.source_row_number,
                lead.created_at.isoformat() if lead.created_at else "",
            ]
        )

    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="leads_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    return response
