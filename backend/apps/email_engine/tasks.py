"""Celery tasks for the SMTP delivery queue."""

from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.email_engine.models import EmailMessageStatus
from apps.email_engine.services import (
    claim_email_message,
    deliver_email,
    mark_email_failed,
    mark_email_retryable,
    mark_email_sent,
    reserve_daily_slot,
)


@shared_task(
    bind=True,
    name="email_engine.send_email_message",
    max_retries=3,
    acks_late=True,
)
def send_email_message(self, message_id: int) -> dict:
    """Send one queued message with idempotent retries.

    Claiming is an atomic status transition. A duplicate Celery delivery sees
    SENT/PROCESSING instead of sending a second SMTP message. A quota slot is
    reserved once per message/day and is reused by retries.
    """
    message = claim_email_message(message_id)
    if message is None:
        return {"status": "ignored", "message_id": message_id}

    if not reserve_daily_slot(message):
        # The global quota is full. Keep the message queued for the next
        # configured window rather than treating a normal quota boundary as a
        # delivery failure.
        from apps.email_engine.services import _next_window_start

        retry_at = _next_window_start(message.campaign, after=timezone.now(), next_day=True)
        mark_email_retryable(
            message_id,
            "Daily marketing e-mail limit reached; deferred to the next sending window.",
            retry_at=retry_at,
        )
        return {"status": "deferred", "message_id": message_id}

    try:
        delivered = deliver_email(message)
        if delivered != 1:
            raise RuntimeError(f"SMTP backend reported {delivered} delivered messages.")
    except Exception as exc:  # provider/network failures are retryable
        retries = int(getattr(self.request, "retries", 0))
        if retries < self.max_retries:
            delay = min(3600, 60 * (2**retries))
            mark_email_retryable(
                message_id,
                str(exc),
                retry_at=timezone.now() + timedelta(seconds=delay),
            )
            raise self.retry(exc=exc, countdown=delay) from exc
        mark_email_failed(message_id, str(exc))
        return {"status": "failed", "message_id": message_id}

    mark_email_sent(message_id)
    return {"status": "sent", "message_id": message_id}


@shared_task(name="email_engine.dispatch_due_email_messages")
def dispatch_due_email_messages(batch_size: int = 100) -> dict:
    """Fan out due queued messages to Celery workers."""
    from apps.email_engine.models import EmailMessage

    now = timezone.now()
    ids = list(
        EmailMessage.objects.filter(
            status=EmailMessageStatus.QUEUED,
            scheduled_at__lte=now,
            campaign__status="RUNNING",
        )
        .order_by("scheduled_at", "id")
        .values_list("id", flat=True)[:batch_size]
    )
    for message_id in ids:
        send_email_message.delay(message_id)
    return {"queued": len(ids)}
