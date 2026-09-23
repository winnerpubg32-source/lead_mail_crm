"""Lead scoring (Phase 5).

Configurable point-based scoring. Every score is clamped to [0, 100].

The rules, from the brief::

    Valid email      +20
    Website          +15
    Contact          +10
    Phone            +10
    Industry         +10
    Location         +10   (city + state present)
    Website reachable+15   (we treat ``normalized_website`` as the proxy until
                           an HTTP probe is added in a later phase)
    Invalid email    -30
    Suppressed       -100
    Unsubscribed    -100
    Bounced          -100

Classifications:

    HOT          >= 70
    WARM         50 – 69
    COLD         20 – 49
    UNQUALIFIED  < 20 (or any blocked e-mail status)

The score is recomputed on demand (typically after import or after an edit)
rather than at every page view, so list queries remain O(1).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.db import models
from django.db.models import Case, F, Q, Value, When

from apps.leads.models import BLOCKED_EMAIL_STATUSES, EmailStatus, Lead

__all__ = [
    "ScoreClassification",
    "ScoreComponents",
    "POINTS",
    "classify_score",
    "compute_lead_score",
    "score_leads_qs",
    "rescore_leads",
]


class ScoreClassification(models.TextChoices):
    HOT = "HOT", "Hot"
    WARM = "WARM", "Warm"
    COLD = "COLD", "Cold"
    UNQUALIFIED = "UNQUALIFIED", "Unqualified"


#: Configurable point values. Kept as a module-level constant so an admin
#: setting can override later.
POINTS = {
    "valid_email": 20,
    "website": 15,
    "contact": 10,
    "phone": 10,
    "industry": 10,
    "location": 10,
    "website_accessible": 15,  # Proxy: website field populated (no live probe yet).
    "invalid_email": -30,
    "suppressed": -100,
    "unsubscribed": -100,
    "bounced": -100,
}


@dataclass
class ScoreComponents:
    """Breakdown of which signals contributed to a lead's score."""

    valid_email: int = 0
    website: int = 0
    contact: int = 0
    phone: int = 0
    industry: int = 0
    location: int = 0
    website_accessible: int = 0
    invalid_email: int = 0
    suppressed: int = 0
    unsubscribed: int = 0
    bounced: int = 0

    @property
    def total(self) -> int:
        return max(0, min(100, sum(getattr(self, k) for k in POINTS)))

    def as_dict(self) -> dict[str, int]:
        return {k: getattr(self, k) for k in POINTS}


def classify_score(score: int, email_status: str = EmailStatus.UNKNOWN) -> str:
    """Return the classification label for a numeric score."""
    if email_status in BLOCKED_EMAIL_STATUSES:
        return ScoreClassification.UNQUALIFIED
    if score >= 70:
        return ScoreClassification.HOT
    if score >= 50:
        return ScoreClassification.WARM
    if score >= 20:
        return ScoreClassification.COLD
    return ScoreClassification.UNQUALIFIED


def compute_lead_score(lead: Lead) -> tuple[int, ScoreComponents]:
    """Compute the score and breakdown for a single lead instance."""
    c = ScoreComponents()

    has_email = bool(lead.normalized_email)
    blocked = lead.email_status in BLOCKED_EMAIL_STATUSES
    has_website = bool(lead.company_id and lead.company.normalized_website)
    has_contact = bool(lead.contact_id and lead.contact.normalized_name)
    has_phone = bool(lead.phone)
    has_industry = bool(lead.industry)
    has_location = bool(lead.city) and bool(lead.state)

    if has_email and lead.email_status == EmailStatus.VALID:
        c.valid_email = POINTS["valid_email"]
    if has_website:
        c.website = POINTS["website"]
        c.website_accessible = POINTS["website_accessible"]
    if has_contact:
        c.contact = POINTS["contact"]
    if has_phone:
        c.phone = POINTS["phone"]
    if has_industry:
        c.industry = POINTS["industry"]
    if has_location:
        c.location = POINTS["location"]
    if lead.email_status == EmailStatus.INVALID:
        c.invalid_email = POINTS["invalid_email"]
    if lead.email_status == EmailStatus.SUPPRESSED:
        c.suppressed = POINTS["suppressed"]
    if lead.email_status == EmailStatus.UNSUBSCRIBED:
        c.unsubscribed = POINTS["unsubscribed"]
    if lead.email_status == EmailStatus.BOUNCED:
        c.bounced = POINTS["bounced"]

    score = c.total
    # Hard-blocked statuses always land at 0 (UNQUALIFIED), regardless of positive
    # signals.
    if blocked:
        score = 0
    return score, c


def score_leads_qs(queryset: Iterable[Lead]) -> dict[int, tuple[int, ScoreComponents]]:
    """
    Bulk score a queryset of leads. Each lead must already have its company and
    contact loaded (``select_related``) so the function does not issue additional
    queries per row.
    """
    result: dict[int, tuple[int, ScoreComponents]] = {}
    for lead in queryset:
        result[lead.pk] = compute_lead_score(lead)
    return result


def rescore_leads(lead_ids: list[int] | None = None, *, batch_size: int = 500) -> int:
    """
    Recompute ``lead_score`` for the given leads (or all active leads when
    ``lead_ids`` is None). Returns the number of rows updated.

    Uses a single UPDATE per lead because the scoring depends on joined data;
    batches keep the transaction short on large tables.
    """
    qs = Lead.objects.exclude(lead_status__in=["MERGED"]).select_related("company", "contact")
    if lead_ids is not None:
        qs = qs.filter(pk__in=lead_ids)

    updated = 0
    for lead in qs.iterator(chunk_size=batch_size):
        score, _ = compute_lead_score(lead)
        if lead.lead_score != score:
            lead.lead_score = score
            lead.save(update_fields=["lead_score", "updated_at"])
            updated += 1
    return updated
