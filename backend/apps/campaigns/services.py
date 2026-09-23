"""Campaign audience preparation and Phase 7 launch orchestration."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from apps.campaigns.models import Campaign, CampaignLead, CampaignStatus
from apps.leads.models import EmailStatus, Lead, LeadStatus

__all__ = [
    "count_eligible_leads",
    "eligible_leads_qs",
    "prepare_campaign",
    "queue_campaign",
    "transition_campaign",
    "validate_campaign_for_launch",
]


def eligible_leads_qs(campaign: Campaign):
    """Return the queryset of leads that match a campaign's audience rules.

    Rules:
      * not MERGED
      * deliverable e-mail (not INVALID/BOUNCED/UNSUBSCRIBED/SUPPRESSED, not empty)
      * lead_score >= minimum_lead_score
      * industry/sub_industry/location matches when specified
    """
    blocked = [
        EmailStatus.INVALID,
        EmailStatus.BOUNCED,
        EmailStatus.UNSUBSCRIBED,
        EmailStatus.SUPPRESSED,
    ]
    qs = (
        Lead.objects.exclude(lead_status__in=[LeadStatus.MERGED, LeadStatus.DO_NOT_CONTACT])
        .exclude(email_status__in=blocked)
        .exclude(Q(contact__isnull=True) | Q(contact__normalized_email=""))
        .select_related("company", "contact")
    )

    if campaign.minimum_lead_score:
        qs = qs.filter(lead_score__gte=campaign.minimum_lead_score)
    if campaign.industry:
        qs = qs.filter(company__industry__iexact=campaign.industry)
    if campaign.sub_industry:
        qs = qs.filter(company__sub_industry__icontains=campaign.sub_industry)
    if campaign.location:
        loc = campaign.location.strip()
        qs = qs.filter(
            Q(company__city__icontains=loc)
            | Q(company__state__icontains=loc)
            | Q(company__country__icontains=loc),
        )
    return qs.distinct()


def count_eligible_leads(campaign: Campaign) -> int:
    return eligible_leads_qs(campaign).count()


def validate_campaign_for_launch(campaign: Campaign) -> list[str]:
    """Return a list of human-readable errors preventing READY/RUNNING."""
    errors: list[str] = []
    if not campaign.name or len(campaign.name.strip()) < 2:
        errors.append("Campaign name is required.")
    if campaign.daily_limit <= 0:
        errors.append("Daily send limit must be positive.")
    if not campaign.template_id:
        errors.append("An email template is required before launching.")
    if (
        campaign.scheduled_end_at
        and campaign.scheduled_start_at
        and campaign.scheduled_end_at <= campaign.scheduled_start_at
    ):
        errors.append("Scheduled end must be after start.")
    if (
        campaign.sending_start_time
        and campaign.sending_end_time
        and campaign.sending_end_time <= campaign.sending_start_time
    ):
        errors.append("Sending end time must be after sending start time.")
    if not count_eligible_leads(campaign):
        errors.append("Audience filters produce zero eligible leads.")
    return errors


@transaction.atomic
def prepare_campaign(campaign: Campaign) -> int:
    """Validate and snapshot the current eligible audience into CampaignLead."""
    if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.PAUSED):
        raise ValidationError(f"Cannot prepare a campaign in {campaign.status} status.")
    errors = validate_campaign_for_launch(campaign)
    if errors:
        raise ValidationError(errors)

    eligible_ids = list(eligible_leads_qs(campaign).values_list("pk", flat=True))
    CampaignLead.objects.filter(campaign=campaign).exclude(lead_id__in=eligible_ids).delete()
    existing = set(CampaignLead.objects.filter(campaign=campaign).values_list("lead_id", flat=True))
    to_create = [
        CampaignLead(
            campaign=campaign, lead_id=lead_id, send_status=CampaignLead.SendStatus.PENDING
        )
        for lead_id in eligible_ids
        if lead_id not in existing
    ]
    CampaignLead.objects.bulk_create(to_create, batch_size=500)

    campaign.eligible_count = len(eligible_ids)
    campaign.transition_to(CampaignStatus.READY)
    campaign.save(update_fields=["status", "eligible_count", "updated_at"])
    return len(eligible_ids)


@transaction.atomic
def queue_campaign(campaign: Campaign) -> int:
    """Render and queue the prepared audience for asynchronous SMTP delivery."""
    from apps.email_engine.services import queue_campaign_messages

    return queue_campaign_messages(campaign)


@transaction.atomic
def transition_campaign(campaign: Campaign, new_status: str) -> Campaign:
    """Transition a campaign and queue messages when it starts running."""
    # Lock the campaign row so two launch requests cannot create duplicate
    # queues or race the status transition.
    campaign = Campaign.objects.select_for_update().select_related("template").get(pk=campaign.pk)

    if new_status == CampaignStatus.READY and campaign.status != CampaignStatus.READY:
        prepare_campaign(campaign)
        return campaign

    if new_status == CampaignStatus.RUNNING:
        if campaign.status == CampaignStatus.DRAFT:
            prepare_campaign(campaign)
            campaign.refresh_from_db()
        errors = validate_campaign_for_launch(campaign)
        if errors:
            raise ValidationError(errors)
        if campaign.memberships.count() == 0:
            prepare_campaign(campaign)
            campaign.refresh_from_db()
        if not campaign.can_transition_to(new_status):
            raise ValidationError(f"Cannot transition from {campaign.status} to {new_status}.")

        campaign.transition_to(CampaignStatus.RUNNING)
        campaign.save(update_fields=["status", "updated_at"])
        queue_campaign(campaign)
        return campaign

    if not campaign.can_transition_to(new_status):
        raise ValidationError(f"Cannot transition campaign from {campaign.status} to {new_status}.")
    campaign.transition_to(new_status)
    campaign.save(update_fields=["status", "updated_at"])

    if new_status == CampaignStatus.CANCELLED:
        from apps.email_engine.models import EmailMessage, EmailMessageStatus

        EmailMessage.objects.filter(
            campaign=campaign,
            status__in=[EmailMessageStatus.QUEUED, EmailMessageStatus.PROCESSING],
        ).update(status=EmailMessageStatus.CANCELLED, updated_at=campaign.updated_at)
        CampaignLead.objects.filter(
            campaign=campaign,
            send_status=CampaignLead.SendStatus.QUEUED,
        ).update(send_status=CampaignLead.SendStatus.SKIPPED, updated_at=campaign.updated_at)
    return campaign
