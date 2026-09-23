"""
Lead model — a company/contact pair moving through the outreach pipeline.

Scope (Phase 2): schema, lifecycle enums and derived fields. Scoring inputs,
campaign execution and suppression enforcement arrive in later phases; the
status/enum vocabulary is fixed here so the API and UI stay stable.
"""

from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company
from apps.contacts.models import Contact
from core.models import TimeStampedModel


class LeadStatus(models.TextChoices):
    """Pipeline state of a lead."""

    NEW = "NEW", _("New")
    QUALIFIED = "QUALIFIED", _("Qualified")
    CONTACTED = "CONTACTED", _("Contacted")
    REPLIED = "REPLIED", _("Replied")
    MEETING = "MEETING", _("Meeting")
    PROPOSAL = "PROPOSAL", _("Proposal")
    WON = "WON", _("Won")
    LOST = "LOST", _("Lost")
    DO_NOT_CONTACT = "DO_NOT_CONTACT", _("Do not contact")
    MERGED = "MERGED", _("Merged")


class EmailStatus(models.TextChoices):
    """Deliverability state of the lead's address."""

    UNKNOWN = "UNKNOWN", _("Unknown")
    VALID = "VALID", _("Valid")
    INVALID = "INVALID", _("Invalid")
    BOUNCED = "BOUNCED", _("Bounced")
    UNSUBSCRIBED = "UNSUBSCRIBED", _("Unsubscribed")
    SUPPRESSED = "SUPPRESSED", _("Suppressed")


#: Statuses that mean "never send marketing e-mail to this lead".
BLOCKED_EMAIL_STATUSES = frozenset(
    {
        EmailStatus.INVALID,
        EmailStatus.BOUNCED,
        EmailStatus.UNSUBSCRIBED,
        EmailStatus.SUPPRESSED,
    }
)


class Lead(TimeStampedModel):
    """A qualified opportunity: one company, one contact, one pipeline state."""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="leads",
        null=True,
        blank=True,
        verbose_name=_("company"),
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        related_name="leads",
        null=True,
        blank=True,
        verbose_name=_("contact"),
    )

    lead_score = models.PositiveSmallIntegerField(_("lead score"), default=0, db_index=True)
    lead_status = models.CharField(
        _("lead status"),
        max_length=20,
        choices=LeadStatus.choices,
        default=LeadStatus.NEW,
        db_index=True,
    )
    email_status = models.CharField(
        _("e-mail status"),
        max_length=20,
        choices=EmailStatus.choices,
        default=EmailStatus.UNKNOWN,
        db_index=True,
    )

    source = models.CharField(_("source"), max_length=120, blank=True, db_index=True)
    # Provenance for imports (Phase 3): which file and row produced this lead.
    source_file = models.CharField(_("source file"), max_length=255, blank=True)
    source_row_number = models.PositiveIntegerField(_("source row number"), null=True, blank=True)

    # When status=MERGED this points to the lead that absorbed this record.
    # Kept as a soft foreign key (no DB constraint) so merges can be rolled
    # back later without a cascade, and the losing lead retains all its
    # provenance columns.
    merged_into = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="merged_from",
        null=True,
        blank=True,
        verbose_name=_("merged into"),
    )
    merged_at = models.DateTimeField(_("merged at"), null=True, blank=True)

    class Meta:
        verbose_name = _("lead")
        verbose_name_plural = _("leads")
        ordering = ("-created_at", "-id")
        indexes = (
            models.Index(fields=["lead_status", "-lead_score"], name="lead_status_score_idx"),
            models.Index(fields=["lead_status", "email_status"], name="lead_status_email_idx"),
            models.Index(fields=["-created_at"], name="lead_created_idx"),
        )
        constraints = (
            models.CheckConstraint(
                condition=Q(lead_score__gte=0) & Q(lead_score__lte=100),
                name="lead_score_between_0_and_100",
            ),
            # One pipeline entry per contact; the same company can appear more
            # than once through different people. Leads without a contact are
            # excluded so manual entries can be created freely.
            models.UniqueConstraint(
                fields=["company", "contact"],
                condition=Q(contact__isnull=False),
                name="lead_unique_contact_per_company",
            ),
        )

    def __str__(self) -> str:
        subject = self.contact.full_name if self.contact_id else "Lead"
        company = self.company.name if self.company_id else "unassigned"
        return f"{subject} @ {company}"

    # -- derived convenience fields (serialised, never stored) ---------------
    @property
    def company_name(self) -> str:
        return self.company.name if self.company_id else ""

    @property
    def contact_name(self) -> str:
        return self.contact.full_name if self.contact_id else ""

    @property
    def job_title(self) -> str:
        return self.contact.job_title if self.contact_id else ""

    @property
    def email(self) -> str:
        return self.contact.email if self.contact_id else ""

    @property
    def normalized_email(self) -> str:
        return self.contact.normalized_email if self.contact_id else ""

    @property
    def phone(self) -> str:
        """Contact phone, falling back to the company switchboard."""
        if self.contact_id and self.contact.phone:
            return self.contact.phone
        return self.company.phone if self.company_id else ""

    @property
    def industry(self) -> str:
        return self.company.industry if self.company_id else ""

    @property
    def city(self) -> str:
        return self.company.city if self.company_id else ""

    @property
    def state(self) -> str:
        return self.company.state if self.company_id else ""

    @property
    def is_contactable(self) -> bool:
        """True when the lead has an address that is safe to send to."""
        return bool(self.normalized_email) and self.email_status not in BLOCKED_EMAIL_STATUSES


# Re-export activity + note models from a single import location.
from apps.leads.activity_models import LeadActivity, LeadNote  # noqa: E402,F401
