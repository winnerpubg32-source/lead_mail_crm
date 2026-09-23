"""SMTP delivery and daily marketing quota services.

The campaign app owns audience preparation. This module owns the persisted
outbound message queue, rendering, atomic quota reservations, and delivery
state transitions used by Celery workers.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from time import sleep
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core.mail import EmailMessage as DjangoEmailMessage
from django.db import OperationalError, transaction
from django.db.models import F
from django.utils import timezone

from apps.campaigns.models import Campaign, CampaignLead, CampaignStatus
from apps.email_engine.models import (
    DailyEmailUsage,
    EmailMessage,
    EmailMessageStatus,
    EmailTemplate,
    render_template,
)
from apps.leads.activity_models import ActivityType
from apps.leads.models import BLOCKED_EMAIL_STATUSES, LeadStatus
from apps.leads.services import record_activity

__all__ = [
    "claim_email_message",
    "daily_usage_payload",
    "deliver_email",
    "mark_email_failed",
    "mark_email_retryable",
    "mark_email_sent",
    "queue_campaign_messages",
    "reserve_daily_slot",
]


# ---------------------------- time and scheduling -------------------------


def _outreach_zone() -> ZoneInfo:
    configured = getattr(settings, "OUTREACH_TIMEZONE", "UTC")
    try:
        return ZoneInfo(configured)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _configured_time(value: str, fallback: time) -> time:
    try:
        hour, minute = (int(part) for part in value.split(":", 1))
        return time(hour=hour, minute=minute)
    except (AttributeError, TypeError, ValueError):
        return fallback


def sending_window(campaign: Campaign) -> tuple[time, time]:
    """Return a campaign's window, falling back to workspace configuration."""
    start = campaign.sending_start_time or _configured_time(
        getattr(settings, "OUTREACH_SENDING_START_TIME", "09:00"), time(9, 0)
    )
    end = campaign.sending_end_time or _configured_time(
        getattr(settings, "OUTREACH_SENDING_END_TIME", "17:00"), time(17, 0)
    )
    return start, end


def _aware(local_date: date, local_time: time) -> datetime:
    return datetime.combine(local_date, local_time, tzinfo=_outreach_zone())


def _next_window_start(
    campaign: Campaign,
    *,
    after: datetime | None = None,
    next_day: bool = False,
) -> datetime:
    """Find the next valid local sending-window start after ``after``."""
    now = after or timezone.now()
    local = now.astimezone(_outreach_zone())
    start_time, end_time = sending_window(campaign)
    if end_time <= start_time:
        raise ValueError("Sending end time must be after sending start time.")

    local_date = local.date() + timedelta(days=1) if next_day else local.date()
    if not next_day:
        if local.time() < start_time:
            return _aware(local_date, start_time)
        if local.time() < end_time:
            return local
        local_date += timedelta(days=1)
    return _aware(local_date, start_time)


def _scheduled_slots(campaign: Campaign, count: int) -> list[datetime]:
    """Spread messages over daily windows, respecting the 90/day guard rail."""
    if count <= 0:
        return []

    start_time, end_time = sending_window(campaign)
    if end_time <= start_time:
        raise ValueError("Sending end time must be after sending start time.")

    now = timezone.now()
    anchor = campaign.scheduled_start_at or now
    if anchor < now:
        anchor = now
    first = _next_window_start(campaign, after=anchor)
    if campaign.scheduled_start_at and campaign.scheduled_start_at > now:
        first = max(first, campaign.scheduled_start_at)

    global_limit = max(1, DailyEmailUsage.configured_limit())
    campaign_limit = campaign.daily_limit or global_limit
    per_day = max(1, min(global_limit, campaign_limit))
    slots: list[datetime] = []
    remaining = count
    window_start = first

    while remaining:
        local_start = window_start.astimezone(_outreach_zone())
        day_end = _aware(local_start.date(), end_time)
        available_seconds = max(1.0, (day_end - window_start).total_seconds())
        batch_size = min(remaining, per_day)
        interval = available_seconds / batch_size
        for index in range(batch_size):
            # Place each message in the middle of its interval instead of
            # issuing a burst at the exact opening of the window.
            candidate = window_start + timedelta(seconds=interval * (index + 0.5))
            slots.append(min(candidate, day_end - timedelta(seconds=1)))
        remaining -= batch_size
        if remaining:
            window_start = _aware(local_start.date() + timedelta(days=1), start_time)

    return slots


# ----------------------------- queue creation ------------------------------


def _lead_context(campaign: Campaign, lead) -> dict[str, str]:
    template = campaign.template
    contact = lead.contact
    company = lead.company
    recommended_service = campaign.recommended_service or (
        template.default_recommended_service if template else ""
    )
    return {
        "first_name": contact.first_name if contact else "",
        "contact_name": lead.contact_name,
        "company_name": lead.company_name,
        "industry": lead.industry,
        "city": lead.city,
        "state": lead.state,
        "website": company.website if company else "",
        "recommended_service": recommended_service,
    }


def _lead_can_receive(lead) -> bool:
    return bool(
        lead.normalized_email
        and lead.lead_status != LeadStatus.MERGED
        and lead.lead_status != LeadStatus.DO_NOT_CONTACT
        and lead.email_status not in BLOCKED_EMAIL_STATUSES
    )


@transaction.atomic
def queue_campaign_messages(campaign: Campaign) -> int:
    """Create one rendered, scheduled EmailMessage per pending membership.

    This is deliberately synchronous database work at launch time. The SMTP
    call is never made here; Celery workers pick up the persisted queue later.
    """
    if not campaign.template_id:
        raise ValueError("An email template is required before queueing messages.")

    memberships = list(
        CampaignLead.objects.select_for_update()
        .filter(campaign=campaign, send_status=CampaignLead.SendStatus.PENDING)
        .select_related("lead", "lead__company", "lead__contact")
        .order_by("id")
    )
    deliverable = []
    skipped = []
    for membership in memberships:
        if _lead_can_receive(membership.lead):
            deliverable.append(membership)
        else:
            skipped.append(membership)

    if skipped:
        CampaignLead.objects.filter(pk__in=[row.pk for row in skipped]).update(
            send_status=CampaignLead.SendStatus.SKIPPED,
            updated_at=timezone.now(),
        )

    slots = _scheduled_slots(campaign, len(deliverable))
    messages = []
    for membership, scheduled_at in zip(deliverable, slots, strict=True):
        lead = membership.lead
        context = _lead_context(campaign, lead)
        template: EmailTemplate = campaign.template
        messages.append(
            EmailMessage(
                campaign=campaign,
                lead=lead,
                to_email=lead.normalized_email,
                subject=render_template(template.subject, context),
                body=render_template(template.body, context),
                status=EmailMessageStatus.QUEUED,
                scheduled_at=scheduled_at,
            )
        )

    if messages:
        # The campaign row is locked by transition_campaign. The constraint is
        # also a final guard if a caller retries this operation.
        EmailMessage.objects.bulk_create(messages, ignore_conflicts=True, batch_size=500)
        CampaignLead.objects.filter(pk__in=[row.pk for row in deliverable]).update(
            send_status=CampaignLead.SendStatus.QUEUED,
            updated_at=timezone.now(),
        )
    return len(messages)


# -------------------------- concurrency-safe quota -------------------------


def reserve_daily_slot(message: EmailMessage, *, for_date: date | None = None) -> bool:
    """Atomically reserve one global marketing slot for this message.

    The conditional UPDATE is the important part: concurrent workers can both
    observe an available row, but only the first 90 conditional updates can
    succeed. A retry of the same message reuses its reservation for that day.
    """
    day = for_date or timezone.now().astimezone(_outreach_zone()).date()
    # The Celery worker claims the message before calling this function, so a
    # duplicate task cannot reserve the same message concurrently. The
    # conditional usage UPDATE is intentionally independent of a long-lived
    # row lock: it is safe on PostgreSQL and avoids turning the quota ledger
    # into a lock convoy on development SQLite databases.
    if EmailMessage.objects.filter(
        pk=message.pk,
        daily_slot_reserved=True,
        daily_slot_date=day,
    ).exists():
        message.daily_slot_reserved = True
        message.daily_slot_date = day
        return True

    updated = 0
    for attempt in range(5):
        try:
            with transaction.atomic():
                usage, _ = DailyEmailUsage.objects.get_or_create(
                    date=day,
                    defaults={"limit": DailyEmailUsage.configured_limit()},
                )
                updated = DailyEmailUsage.objects.filter(
                    pk=usage.pk, sent_count__lt=F("limit")
                ).update(sent_count=F("sent_count") + 1, updated_at=timezone.now())
            break
        except OperationalError:
            # SQLite can report a transient table lock in local concurrent
            # tests; PostgreSQL may similarly surface a short serialization
            # conflict. Retry the small reservation transaction, never the
            # SMTP operation.
            if attempt == 4:
                raise
            sleep(0.01 * (attempt + 1))
    if not updated:
        return False

    EmailMessage.objects.filter(pk=message.pk).update(
        daily_slot_reserved=True,
        daily_slot_date=day,
        updated_at=timezone.now(),
    )
    message.daily_slot_reserved = True
    message.daily_slot_date = day
    return True


def daily_usage_payload(campaign: Campaign | None = None) -> dict:
    """Return dashboard-safe quota data without exposing SMTP configuration."""
    day = timezone.now().astimezone(_outreach_zone()).date()
    usage = DailyEmailUsage.objects.filter(date=day).first()
    limit = usage.limit if usage else DailyEmailUsage.configured_limit()
    reserved = usage.sent_count if usage else 0
    messages = EmailMessage.objects.filter(created_at__date=day)
    if campaign is not None:
        messages = messages.filter(campaign=campaign)
    queued = messages.filter(status=EmailMessageStatus.QUEUED).count()
    failed = messages.filter(status=EmailMessageStatus.FAILED).count()
    start, end = (
        sending_window(campaign)
        if campaign
        else (
            _configured_time(getattr(settings, "OUTREACH_SENDING_START_TIME", "09:00"), time(9, 0)),
            _configured_time(getattr(settings, "OUTREACH_SENDING_END_TIME", "17:00"), time(17, 0)),
        )
    )
    return {
        "date": day.isoformat(),
        "sent_today": reserved,
        "limit": limit,
        "remaining": max(0, limit - reserved),
        "progress_pct": min(100, round(reserved * 100 / limit)) if limit else 100,
        "queued": queued,
        "failed": failed,
        "window_label": f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')} (workspace timezone)",
    }


# --------------------------- delivery state machine ------------------------


def claim_email_message(message_id: int, *, now: datetime | None = None) -> EmailMessage | None:
    """Claim a due queued message exactly once for processing."""
    current = now or timezone.now()
    updated = EmailMessage.objects.filter(
        pk=message_id,
        status=EmailMessageStatus.QUEUED,
        scheduled_at__lte=current,
        campaign__status=CampaignStatus.RUNNING,
    ).update(
        status=EmailMessageStatus.PROCESSING,
        attempt_count=F("attempt_count") + 1,
        updated_at=current,
    )
    if not updated:
        return None
    return EmailMessage.objects.select_related("campaign", "lead").get(pk=message_id)


def deliver_email(message: EmailMessage) -> int:
    """Send one message through Django's configured e-mail backend."""
    mail = DjangoEmailMessage(
        subject=message.subject,
        body=message.body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[message.to_email],
    )
    return mail.send(fail_silently=False)


@transaction.atomic
def mark_email_sent(message_id: int) -> bool:
    """Persist success and increment campaign counters idempotently."""
    message = EmailMessage.objects.select_for_update().select_related("lead").get(pk=message_id)
    if message.status == EmailMessageStatus.SENT:
        return False
    if message.status != EmailMessageStatus.PROCESSING:
        return False

    sent_at = timezone.now()
    message.status = EmailMessageStatus.SENT
    message.sent_at = sent_at
    message.error_message = ""
    message.save(update_fields=["status", "sent_at", "error_message", "updated_at"])

    membership_updated = CampaignLead.objects.filter(
        campaign_id=message.campaign_id,
        lead_id=message.lead_id,
        send_status__in=[CampaignLead.SendStatus.PENDING, CampaignLead.SendStatus.QUEUED],
    ).update(
        send_status=CampaignLead.SendStatus.SENT,
        sent_at=sent_at,
        updated_at=sent_at,
    )
    if membership_updated:
        Campaign.objects.filter(pk=message.campaign_id).update(
            sent_count=F("sent_count") + 1,
            updated_at=sent_at,
        )
        record_activity(
            message.lead,
            ActivityType.EMAIL_SENT,
            title="Campaign email sent",
            metadata={
                "campaign_id": message.campaign_id,
                "email_message_id": message.pk,
                "to_email": message.to_email,
            },
            actor="email_engine",
        )
    return True


def mark_email_retryable(message_id: int, error: str, *, retry_at: datetime) -> None:
    EmailMessage.objects.filter(pk=message_id, status=EmailMessageStatus.PROCESSING).update(
        status=EmailMessageStatus.QUEUED,
        scheduled_at=retry_at,
        error_message=error[:2000],
        updated_at=timezone.now(),
    )


def mark_email_failed(message_id: int, error: str) -> None:
    with transaction.atomic():
        message = EmailMessage.objects.select_for_update().get(pk=message_id)
        if message.status == EmailMessageStatus.SENT:
            return
        message.status = EmailMessageStatus.FAILED
        message.error_message = error[:2000]
        message.save(update_fields=["status", "error_message", "updated_at"])
        CampaignLead.objects.filter(
            campaign_id=message.campaign_id,
            lead_id=message.lead_id,
            send_status=CampaignLead.SendStatus.QUEUED,
        ).update(send_status=CampaignLead.SendStatus.SKIPPED, updated_at=timezone.now())
