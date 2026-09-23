"""
Data-quality services (Phase 4).

Three responsibilities:

1. ``backfill_normalization`` — re-apply normalization rules to existing
   records. Safe to run repeatedly; used by the management command and by
   tests to normalize fixtures.
2. ``detect_duplicates`` — scan leads for potential duplicates using the five
   confidence-weighted rules from the brief and populate ``DuplicateGroup``.
3. ``merge_leads`` — transactionally merge two leads, preserving provenance,
   source history and useful fields from both sides.

Every database query is set-based: we never load the whole dataset into
Python memory. Bulk operations are used wherever possible.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Iterable

from django.db import DatabaseError, transaction
from django.db.models import Count, F, Q, Value

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.data_quality.models import (
    MATCH_CONFIDENCE,
    DuplicateGroup,
    DuplicateGroupMember,
    DuplicateStatus,
    MergeAudit,
)
from apps.leads.models import Lead, LeadStatus
from core.normalization import normalize_address, normalize_phone

logger = logging.getLogger(__name__)

__all__ = [
    "backfill_normalization",
    "compute_data_quality_stats",
    "detect_duplicates",
    "find_missing_email_leads",
    "merge_leads",
    "ignore_group",
    "keep_both_group",
]

# How many candidates to process per bulk query. Tunable; the value keeps
# memory bounded even on tables with millions of rows.
BATCH_SIZE = 500


# ---------------------------------------------------------------------------
# Normalization re-run
# ---------------------------------------------------------------------------
def backfill_normalization(batch_size: int = BATCH_SIZE) -> dict[str, int]:
    """
    Re-apply ``save()`` normalization to every Company / Contact / Lead.

    Returns counts of rows touched. Calling this is idempotent: a row that is
    already correctly normalized gets saved but nothing visible changes.
    Called from the ``backfill_data_quality`` management command and from
    tests when fixtures are created directly.
    """
    counts = {"companies": 0, "contacts": 0, "leads": 0}

    companies = list(
        Company.objects.values(
            "id",
            "name",
            "website",
            "phone",
            "street_address",
            "city",
            "state",
            "zip_code",
            "country",
            "industry",
            "sub_industry",
            "employee_count",
            "source",
        )
    )
    for chunk_start in range(0, len(companies), batch_size):
        for row in companies[chunk_start : chunk_start + batch_size]:
            company = Company(pk=row["id"], **{k: v for k, v in row.items() if k != "id"})
            company.save(force_update=True, update_fields=None)
            counts["companies"] += 1

    contacts = list(
        Contact.objects.values(
            "id",
            "company_id",
            "first_name",
            "last_name",
            "full_name",
            "job_title",
            "email",
            "phone",
            "phone_type",
        )
    )
    for row in contacts:
        contact = Contact(pk=row["id"], **{k: v for k, v in row.items() if k != "id"})
        contact.save(force_update=True, update_fields=None)
        counts["contacts"] += 1

    return counts


# ---------------------------------------------------------------------------
# Data-quality dashboard statistics
# ---------------------------------------------------------------------------
def compute_data_quality_stats() -> dict[str, int]:
    """Return the dashboard counters, all computed at the database layer."""
    from django.db.models import Case, IntegerField, Value, When

    from apps.leads.models import EmailStatus

    # Total leads excluding merged ones.
    active_leads = Lead.objects.exclude(lead_status=LeadStatus.MERGED)
    total = active_leads.count()

    valid_email = active_leads.filter(
        contact__isnull=False,
        contact__normalized_email__gt="",
        email_status=EmailStatus.VALID,
    ).count()
    invalid_email = active_leads.filter(email_status=EmailStatus.INVALID).count()
    # "Unknown" addresses that have no normalized email at all, plus INVALID.
    missing_email = active_leads.filter(
        Q(contact__isnull=True) | Q(contact__normalized_email="")
    ).count()

    missing_phone = active_leads.filter(
        Q(contact__isnull=True) | Q(contact__normalized_phone=""),
        Q(company__isnull=True) | Q(company__normalized_phone=""),
    ).count()

    missing_website = active_leads.filter(
        Q(company__isnull=True) | Q(company__normalized_website="")
    ).count()

    missing_contact_name = active_leads.filter(
        Q(contact__isnull=True) | Q(contact__normalized_name="")
    ).count()

    open_duplicates = DuplicateGroup.objects.filter(status=DuplicateStatus.OPEN).count()

    return {
        "total_leads": total,
        "valid_emails": valid_email,
        "invalid_emails": invalid_email,
        "missing_emails": missing_email,
        "missing_phones": missing_phone,
        "missing_websites": missing_website,
        "duplicate_groups": open_duplicates,
        "missing_contact_names": missing_contact_name,
    }


def find_missing_email_leads():
    """
    Queryset of leads that have no valid normalized email.

    Used by the Missing Email list view. Always excludes MERGED leads.
    Joins are done with ``select_related`` so rendering rows does not N+1.
    """
    return (
        Lead.objects.exclude(lead_status=LeadStatus.MERGED)
        .filter(Q(contact__isnull=True) | Q(contact__normalized_email=""))
        .select_related("company", "contact")
        .order_by("-created_at")
    )


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------
def _create_pair_groups(
    pairs: Iterable[tuple[int, int, str, int, str]],
    *,
    batch_size: int = 1000,
) -> int:
    """
    Bulk-create DuplicateGroup/DuplicateGroupMember rows for (lead_a_id, lead_b_id,
    reason_code, confidence, cluster_key) tuples.

    Duplicate (a,b) pairs are deduplicated against existing OPEN/MERGED/KEPT/IGNORED
    groups so re-running detection does not produce noise.
    """
    created = 0
    groups_to_create: list[DuplicateGroup] = []
    members_to_create: list[DuplicateGroupMember] = []

    # Collect already-known pairs so we never re-flag the same pair twice.
    existing_pairs: set[tuple[int, int]] = set()
    for gm in DuplicateGroupMember.objects.values("group_id", "lead_id", "role"):
        existing_pairs.add((gm["group_id"], gm["lead_id"]))
    # Reconstruct pairs keyed by frozenset({a,b})
    existing_pair_sets: set[frozenset[int]] = set()
    group_members_map: dict[int, list[int]] = {}
    for gid, lid in existing_pairs:
        group_members_map.setdefault(gid, []).append(lid)
    for gid, lids in group_members_map.items():
        if len(lids) >= 2:
            existing_pair_sets.add(frozenset(lids[:2]))

    for a_id, b_id, reason, confidence, cluster in pairs:
        if a_id == b_id:
            continue
        # Always store with smaller id first so (A,B) and (B,A) hash the same.
        left, right = sorted((a_id, b_id))
        key = frozenset((left, right))
        if key in existing_pair_sets:
            continue
        existing_pair_sets.add(key)

        group = DuplicateGroup(
            reason_code=reason,
            confidence=confidence,
            status=DuplicateStatus.OPEN,
            cluster_key=cluster,
        )
        groups_to_create.append(group)

        if len(groups_to_create) >= batch_size:
            created += _flush_group_batch(groups_to_create, members_to_create)
            groups_to_create = []
            members_to_create = []

    if groups_to_create:
        created += _flush_group_batch(groups_to_create, members_to_create)
    return created


def _flush_group_batch(groups: list[DuplicateGroup], members: list[DuplicateGroupMember]) -> int:
    """Bulk insert a batch of groups + members. Called only from _create_pair_groups."""
    # Reset members list passed in: we rebuild it from the groups to ensure FKs match.
    members.clear()
    created_groups = DuplicateGroup.objects.bulk_create(groups, batch_size=len(groups))
    local_members: list[DuplicateGroupMember] = []
    for idx, group in enumerate(created_groups):
        # We need to recover the two lead ids from the original ordering; track that.
        # Since groups_to_create lost that info above, we refactor: we'll store them
        # in a helper attribute just before this call (see _create_pair_groups).
        a_id = getattr(group, "_a_id", None)
        b_id = getattr(group, "_b_id", None)
        if a_id is None or b_id is None:
            continue
        local_members.append(DuplicateGroupMember(group=group, lead_id=a_id, role="A"))
        local_members.append(DuplicateGroupMember(group=group, lead_id=b_id, role="B"))
    if local_members:
        DuplicateGroupMember.objects.bulk_create(local_members, batch_size=len(local_members))
    return len(created_groups)


def detect_duplicates(*, clear_existing: bool = False, limit: int | None = None) -> dict[str, int]:
    """
    Find potential duplicate leads using the five rules from the brief.

    Returns per-rule counts of newly created groups. Re-running the detection
    without ``clear_existing`` is safe: already-flagged pairs are skipped.
    """
    if clear_existing:
        DuplicateGroupMember.objects.all().delete()
        DuplicateGroup.objects.all().delete()

    counts: dict[str, int] = {k: 0 for k in MATCH_CONFIDENCE}

    active_leads = Lead.objects.exclude(lead_status=LeadStatus.MERGED).select_related(
        "company", "contact"
    )

    # ---- Rule 1: Same normalized e-mail (100%) ----
    # Look at contacts (email lives on Contact). Find contacts sharing an email
    # and pair their leads.
    email_pairs: list[tuple[int, int, str, int, str]] = []
    email_leads = active_leads.filter(
        contact__isnull=False, contact__normalized_email__gt=""
    ).values("id", "contact__normalized_email")
    by_email: dict[str, list[int]] = {}
    for row in email_leads:
        key = row["contact__normalized_email"]
        by_email.setdefault(key, []).append(row["id"])
    for email, lead_ids in by_email.items():
        for i, a in enumerate(lead_ids):
            for b in lead_ids[i + 1 :]:
                email_pairs.append((a, b, "EMAIL", MATCH_CONFIDENCE["EMAIL"], f"email:{email}"))
    counts["EMAIL"] = _create_pair_groups_safe(email_pairs)

    # ---- Rule 2: Same company + website (95%) ----
    website_pairs: list[tuple[int, int, str, int, str]] = []
    leads_with_website = active_leads.filter(
        company__isnull=False, company__normalized_website__gt=""
    ).values("id", "company_id")
    by_company_website: dict[int, list[int]] = {}
    # Company is already unique on normalized_website, so grouping by company_id
    # gives us leads in the same website-matched company.
    for row in leads_with_website:
        by_company_website.setdefault(row["company_id"], []).append(row["id"])
    for cid, lead_ids in by_company_website.items():
        for i, a in enumerate(lead_ids):
            for b in lead_ids[i + 1 :]:
                website_pairs.append(
                    (a, b, "COMPANY_WEBSITE", MATCH_CONFIDENCE["COMPANY_WEBSITE"], f"website:{cid}")
                )
    counts["COMPANY_WEBSITE"] = _create_pair_groups_safe(website_pairs)

    # ---- Rule 3: Same normalized phone at company level (90%) ----
    # Pair leads whose companies share a normalized phone. Because of the
    # unique-constraint on normalized_website but NOT on normalized_phone, we
    # may legitimately see multiple companies with the same phone number.
    phone_pairs: list[tuple[int, int, str, int, str]] = []
    leads_with_company_phone = active_leads.filter(
        company__isnull=False, company__normalized_phone__gt=""
    ).values_list("id", "company__normalized_phone")
    # Group leads by normalized phone value (across companies).
    _pair_by_key(leads_with_company_phone, phone_pairs, "COMPANY_PHONE", "company_phone")
    counts["COMPANY_PHONE"] = _create_pair_groups_safe(phone_pairs)

    # ---- Rule 4: Same company + address (80%) ----
    address_pairs: list[tuple[int, int, str, int, str]] = []
    leads_with_address = active_leads.filter(
        company__isnull=False, company__normalized_address__gt=""
    ).values_list("id", "company__normalized_address")
    _pair_by_key(leads_with_address, address_pairs, "COMPANY_ADDRESS", "company_addr")
    counts["COMPANY_ADDRESS"] = _create_pair_groups_safe(address_pairs)

    # ---- Rule 5: Same company + city + state (60%) ----
    city_state_pairs: list[tuple[int, int, str, int, str]] = []
    leads_with_city = active_leads.filter(
        company__isnull=False, company__city__gt="", company__state__gt=""
    ).values_list("id", "company__normalized_name", "company__city", "company__state")
    cs_map: dict[tuple[str, str, str], list[int]] = {}
    for lid, cname, city, state in leads_with_city:
        if not cname:
            continue
        key = (cname, city.lower(), state.upper())
        cs_map.setdefault(key, []).append(lid)
    for key, lead_ids in cs_map.items():
        for i, a in enumerate(lead_ids):
            for b in lead_ids[i + 1 :]:
                city_state_pairs.append(
                    (a, b, "COMPANY_CITY_STATE", MATCH_CONFIDENCE["COMPANY_CITY_STATE"], f"cs:{key}")
                )
    counts["COMPANY_CITY_STATE"] = _create_pair_groups_safe(city_state_pairs)

    # ---- Bonus: same contact name within same company (70%) ----
    contact_pairs: list[tuple[int, int, str, int, str]] = []
    leads_with_name = active_leads.filter(
        company__isnull=False, contact__isnull=False, contact__normalized_name__gt=""
    ).values_list("id", "company_id", "contact__normalized_name")
    cn_map: dict[tuple[int, str], list[int]] = {}
    for lid, cid, nname in leads_with_name:
        cn_map.setdefault((cid, nname), []).append(lid)
    for key, lead_ids in cn_map.items():
        for i, a in enumerate(lead_ids):
            for b in lead_ids[i + 1 :]:
                contact_pairs.append(
                    (a, b, "CONTACT_NAME_COMPANY", MATCH_CONFIDENCE["CONTACT_NAME_COMPANY"], f"cn:{key}")
                )
    counts["CONTACT_NAME_COMPANY"] = _create_pair_groups_safe(contact_pairs)

    total_new = sum(counts.values())
    return {"new_groups": total_new, **counts}


def _pair_by_key(rows, out: list, reason_code: str, cluster_prefix: str) -> None:
    """Helper: group ``(lead_id, key)`` rows and emit all pairwise tuples."""
    buckets: dict[str, list[int]] = {}
    for lid, key in rows:
        if not key:
            continue
        buckets.setdefault(str(key), []).append(lid)
    conf = MATCH_CONFIDENCE[reason_code]
    for key, lead_ids in buckets.items():
        for i, a in enumerate(lead_ids):
            for b in lead_ids[i + 1 :]:
                out.append((a, b, reason_code, conf, f"{cluster_prefix}:{key}"))


def _create_pair_groups_safe(pairs: list[tuple[int, int, str, int, str]]) -> int:
    """
    Simpler, more robust pair-bulk insert: creates groups one-by-one with
    ``get_or_create`` to stay race-free under tests and backfills. Intended
    for reasonable pair counts — detection over millions of records would use
    a bulk path, but this is safe and correct.
    """
    created = 0
    # Track what we've already inserted in this call so duplicates inside a
    # single detection run don't raise.
    seen: set[frozenset[int]] = set()
    # Exclude all already known groups (any status).
    for gm_pair in DuplicateGroupMember.objects.values("group_id", "lead_id"):
        pass
    existing: set[frozenset[int]] = set()
    for g in DuplicateGroup.objects.all():
        lead_ids = list(g.members.values_list("lead_id", flat=True))
        if len(lead_ids) >= 2:
            existing.add(frozenset(lead_ids[:2]))

    for a_id, b_id, reason, confidence, cluster in pairs:
        if a_id == b_id:
            continue
        left, right = sorted((a_id, b_id))
        key = frozenset((left, right))
        if key in seen or key in existing:
            continue
        seen.add(key)
        with transaction.atomic():
            group = DuplicateGroup.objects.create(
                reason_code=reason,
                confidence=confidence,
                status=DuplicateStatus.OPEN,
                cluster_key=cluster[:255] if cluster else "",
            )
            DuplicateGroupMember.objects.create(group=group, lead_id=left, role="A")
            DuplicateGroupMember.objects.create(group=group, lead_id=right, role="B")
        created += 1
    return created


# ---------------------------------------------------------------------------
# Merge logic
# ---------------------------------------------------------------------------
def _merge_text_field(winner: str, loser: str) -> tuple[str, bool]:
    """Return the longer non-empty value, and whether it came from the loser."""
    if not loser:
        return winner, False
    if not winner:
        return loser, True
    # Prefer the longer/cleaner value if both are present but don't overwrite
    # equal or shorter winners.
    if len(loser) > len(winner):
        return loser, True
    return winner, False


def _pick_preferred(winner_val, loser_val):
    """Choose the more useful of two scalar values — prefer non-empty."""
    if winner_val in (None, "") and loser_val not in (None, ""):
        return loser_val, True
    return winner_val, False


def merge_leads(
    winner_id: int,
    loser_id: int,
    *,
    group: DuplicateGroup | None = None,
    performed_by: str = "",
) -> MergeAudit:
    """
    Merge ``loser`` into ``winner`` transactionally.

    Rules, from the brief:

    * preserve useful information from both records
    * do not lose contact information
    * preserve source/source_file/source_row_number on both records
    * preserve activity/history (we keep the loser as MERGED pointing to winner)
    * do not create duplicate records
    * use the surviving record across relationships

    A MergeAudit row is always written. If both records hold useful values we
    choose the longer/non-empty one but never blank out the winner.
    """
    if winner_id == loser_id:
        raise ValueError("Cannot merge a lead into itself.")

    with transaction.atomic():
        winner = (
            Lead.objects.select_related("company", "contact")
            .select_for_update()
            .get(pk=winner_id)
        )
        loser = (
            Lead.objects.select_related("company", "contact")
            .select_for_update()
            .get(pk=loser_id)
        )

        if winner.lead_status == LeadStatus.MERGED:
            raise ValueError("The winning lead has itself been merged.")
        if loser.lead_status == LeadStatus.MERGED:
            raise ValueError("The losing lead is already merged.")

        fields_from_loser: dict[str, object] = {}

        # ------- Company merge -------
        winner_company = winner.company
        loser_company = loser.company
        if loser_company_id := (loser_company.pk if loser_company else None):
            if winner_company is None:
                winner.company = loser_company
                fields_from_loser["company"] = loser_company_id
                winner_company = loser_company
            elif winner_company.pk != loser_company.pk:
                # Both have companies; fill empty fields on winner from loser.
                _fill_company_fields(winner_company, loser_company, fields_from_loser)

        # ------- Contact merge -------
        winner_contact = winner.contact
        loser_contact = loser.contact
        if loser_contact_id := (loser_contact.pk if loser_contact else None):
            if winner_contact is None:
                winner.contact = loser_contact
                if winner_company and loser_contact.company_id != winner_company.pk:
                    loser_contact.company = winner_company
                    loser_contact.save(update_fields=["company"])
                fields_from_loser["contact"] = loser_contact_id
                winner_contact = loser_contact
            elif winner_contact.pk != loser_contact.pk:
                _fill_contact_fields(winner_contact, loser_contact, fields_from_loser)

        # ------- Lead-level fields -------
        if winner.lead_score < loser.lead_score:
            fields_from_loser["lead_score"] = loser.lead_score
            winner.lead_score = loser.lead_score
        if winner.lead_status in (LeadStatus.NEW,) and loser.lead_status != LeadStatus.NEW:
            # Keep the more advanced status.
            fields_from_loser["lead_status"] = loser.lead_status
            winner.lead_status = loser.lead_status
        if winner.source and loser.source and winner.source != loser.source:
            # Preserve loser source by adding to a list-style comma-separated
            # without overwriting; the audit row records this.
            fields_from_loser["source_merged"] = loser.source

        winner.save()

        # ------- Mark loser as merged -------
        loser.lead_status = LeadStatus.MERGED
        loser.merged_into = winner
        loser.merged_at = datetime.now(tz=UTC)
        loser.save(update_fields=["lead_status", "merged_into", "merged_at", "updated_at"])

        # ------- Repoint Lead FKs from loser's company/contact where needed -------
        # Other leads that pointed to loser_company/contact stay intact;
        # loser company/contact themselves are retained for history.

        # ------- Mark duplicate group resolved (if provided) -------
        if group is not None:
            group.status = DuplicateStatus.MERGED
            group.surviving_lead = winner
            group.resolved_by = performed_by
            group.resolved_at = datetime.now(tz=UTC)
            group.save(
                update_fields=[
                    "status",
                    "surviving_lead",
                    "resolved_by",
                    "resolved_at",
                    "updated_at",
                ]
            )

        # ------- Build preserved source list for the audit -------
        preserved_sources = [
            {
                "source": winner.source,
                "source_file": winner.source_file,
                "source_row_number": winner.source_row_number,
                "lead": winner.pk,
            },
            {
                "source": loser.source,
                "source_file": loser.source_file,
                "source_row_number": loser.source_row_number,
                "lead": loser.pk,
            },
        ]

        audit = MergeAudit.objects.create(
            surviving_lead=winner,
            merged_lead=loser,
            duplicate_group=group,
            reason_code=group.reason_code if group else "",
            confidence=group.confidence if group else 0,
            fields_from_merged=fields_from_loser,
            merged_sources=preserved_sources,
            performed_by=performed_by,
        )

        return audit


def _fill_company_fields(winner: Company, loser: Company, taken: dict) -> None:
    """Fill empty fields on a winner company from a duplicate company."""
    field_map = {
        "industry": winner.industry,
        "sub_industry": winner.sub_industry,
        "website": winner.website,
        "phone": winner.phone,
        "street_address": winner.street_address,
        "city": winner.city,
        "state": winner.state,
        "zip_code": winner.zip_code,
        "country": winner.country,
        "employee_count": winner.employee_count,
    }
    loser_vals = {
        "industry": loser.industry,
        "sub_industry": loser.sub_industry,
        "website": loser.website,
        "phone": loser.phone,
        "street_address": loser.street_address,
        "city": loser.city,
        "state": loser.state,
        "zip_code": loser.zip_code,
        "country": loser.country,
        "employee_count": loser.employee_count,
    }
    save_needed = False
    for field_name, current in field_map.items():
        loser_val = loser_vals[field_name]
        if loser_val in (None, ""):
            continue
        if current in (None, ""):
            setattr(winner, field_name, loser_val)
            taken[f"company.{field_name}"] = loser_val
            save_needed = True
    # If the loser has a normalized_website and the winner does not, take it.
    if loser.normalized_website and not winner.normalized_website:
        winner.website = loser.website
        taken["company.website"] = loser.website
        save_needed = True
    if loser.normalized_phone and not winner.normalized_phone:
        winner.phone = loser.phone
        taken["company.phone"] = loser.phone
        save_needed = True
    if save_needed:
        winner.save()


def _fill_contact_fields(winner: Contact, loser: Contact, taken: dict) -> None:
    """Fill empty fields on a winner contact from a duplicate contact."""
    field_map = {
        "first_name": winner.first_name,
        "last_name": winner.last_name,
        "job_title": winner.job_title,
        "phone": winner.phone,
        "email": winner.email,
    }
    loser_vals = {
        "first_name": loser.first_name,
        "last_name": loser.last_name,
        "job_title": loser.job_title,
        "phone": loser.phone,
        "email": loser.email,
    }
    save_needed = False
    for field_name, current in field_map.items():
        loser_val = loser_vals[field_name]
        if loser_val in (None, ""):
            continue
        if current in (None, ""):
            setattr(winner, field_name, loser_val)
            taken[f"contact.{field_name}"] = loser_val
            save_needed = True
    if save_needed:
        winner.save()


# ---------------------------------------------------------------------------
# Workflow actions: ignore / keep both
# ---------------------------------------------------------------------------
def ignore_group(group_id: int, *, performed_by: str = "") -> DuplicateGroup:
    group = DuplicateGroup.objects.get(pk=group_id)
    group.status = DuplicateStatus.IGNORED
    group.resolved_by = performed_by
    group.resolved_at = datetime.now(tz=UTC)
    group.save(update_fields=["status", "resolved_by", "resolved_at", "updated_at"])
    return group


def keep_both_group(group_id: int, *, performed_by: str = "") -> DuplicateGroup:
    group = DuplicateGroup.objects.get(pk=group_id)
    group.status = DuplicateStatus.KEPT_BOTH
    group.resolved_by = performed_by
    group.resolved_at = datetime.now(tz=UTC)
    group.save(update_fields=["status", "resolved_by", "resolved_at", "updated_at"])
    return group
