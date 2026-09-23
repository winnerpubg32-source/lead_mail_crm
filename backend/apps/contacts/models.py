"""
Contact model — the person behind a company record.

Scope (Phase 2): schema + normalisation. E-mail verification, enrichment and
suppression checks belong to later phases.
"""

from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company
from core.models import TimeStampedModel
from core.normalization import (
    build_full_name,
    normalize_contact_name,
    normalize_email,
    normalize_name_case,
    normalize_phone,
    normalize_whitespace,
)


class PhoneType(models.TextChoices):
    """What kind of number ``phone`` holds — decides dialling priority later."""

    UNKNOWN = "UNKNOWN", _("Unknown")
    MOBILE = "MOBILE", _("Mobile")
    LANDLINE = "LANDLINE", _("Landline")
    OFFICE = "OFFICE", _("Office")
    OTHER = "OTHER", _("Other")


class Contact(TimeStampedModel):
    """A person attached to a company (decision maker, gatekeeper, …)."""

    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        related_name="contacts",
        null=True,
        blank=True,
        verbose_name=_("company"),
    )

    first_name = models.CharField(_("first name"), max_length=120, blank=True)
    last_name = models.CharField(_("last name"), max_length=120, blank=True)
    # Denormalised for sorting and for the table's "Contact" column.
    full_name = models.CharField(_("full name"), max_length=255, blank=True, db_index=True)
    # Matching key — lowercase, stripped, accent-folded.
    normalized_name = models.CharField(
        _("normalized name"), max_length=255, blank=True, editable=False, db_index=True
    )

    job_title = models.CharField(_("job title"), max_length=180, blank=True, db_index=True)

    email = models.EmailField(_("e-mail"), max_length=320, blank=True)
    # Matching key — lowercase, trimmed.
    normalized_email = models.CharField(
        _("normalized e-mail"), max_length=320, blank=True, editable=False, db_index=True
    )

    phone = models.CharField(_("phone"), max_length=50, blank=True)
    normalized_phone = models.CharField(
        _("normalized phone"), max_length=32, blank=True, editable=False, db_index=True
    )
    phone_type = models.CharField(
        _("phone type"), max_length=16, choices=PhoneType.choices, default=PhoneType.UNKNOWN
    )

    class Meta:
        verbose_name = _("contact")
        verbose_name_plural = _("contacts")
        ordering = ("full_name", "id")
        indexes = (
            models.Index(fields=["last_name", "first_name"], name="contact_name_idx"),
            models.Index(fields=["company", "full_name"], name="contact_company_name_idx"),
            models.Index(fields=["company", "normalized_name"], name="contact_company_norm_name_idx"),
        )
        constraints = (
            # A company cannot hold the same e-mail address twice; contacts
            # without a company or without an e-mail are unaffected.
            models.UniqueConstraint(
                fields=["company", "normalized_email"],
                condition=Q(company__isnull=False) & ~Q(normalized_email=""),
                name="contact_unique_email_per_company",
            ),
        )

    def __str__(self) -> str:
        return self.full_name or self.email or f"Contact #{self.pk}"

    def save(self, *args, **kwargs):
        self.first_name = normalize_whitespace(self.first_name)
        self.last_name = normalize_whitespace(self.last_name)

        # Light title-casing for cosmetic purposes (never invents data).
        if self.first_name and self.first_name == self.first_name.lower():
            self.first_name = normalize_name_case(self.first_name)
        if self.last_name and self.last_name == self.last_name.lower():
            self.last_name = normalize_name_case(self.last_name)

        computed = build_full_name(self.first_name, self.last_name)
        self.full_name = normalize_whitespace(self.full_name) or computed

        self.job_title = normalize_whitespace(self.job_title)
        self.email = normalize_whitespace(self.email).lower()
        self.normalized_email = normalize_email(self.email)
        self.normalized_phone = normalize_phone(self.phone)
        self.normalized_name = normalize_contact_name(self.first_name, self.last_name)

        super().save(*args, **kwargs)

    @property
    def company_name(self) -> str:
        return self.company.name if self.company_id else ""

    @property
    def has_email(self) -> bool:
        return bool(self.normalized_email)
