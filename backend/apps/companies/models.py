"""
Company model — the business record every contact and lead hangs off.

Scope (Phase 2): schema + normalisation only. Import ingestion, dedup merges and
enrichment arrive in later phases — this module defines the shape they will
write into.
"""

from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel
from core.normalization import (
    normalize_address,
    normalize_company_name,
    normalize_domain,
    normalize_phone,
    normalize_state,
    normalize_whitespace,
)


class Company(TimeStampedModel):
    """An imported or manually created business."""

    name = models.CharField(_("company name"), max_length=255, db_index=True)
    # Matching key — see core.normalization.normalize_company_name.
    normalized_name = models.CharField(
        _("normalized name"), max_length=255, blank=True, editable=False, db_index=True
    )

    industry = models.CharField(_("industry"), max_length=150, blank=True, db_index=True)
    sub_industry = models.CharField(_("sub industry"), max_length=150, blank=True)

    website = models.URLField(_("website"), max_length=500, blank=True)
    # Bare host ("acme.com") — the dedup key for imported datasets.
    normalized_website = models.CharField(
        _("normalized website"), max_length=255, blank=True, editable=False, db_index=True
    )

    phone = models.CharField(_("phone"), max_length=50, blank=True)
    normalized_phone = models.CharField(
        _("normalized phone"), max_length=32, blank=True, editable=False, db_index=True
    )

    street_address = models.CharField(_("street address"), max_length=255, blank=True)
    city = models.CharField(_("city"), max_length=120, blank=True, db_index=True)
    state = models.CharField(_("state"), max_length=120, blank=True, db_index=True)
    zip_code = models.CharField(_("zip code"), max_length=20, blank=True)
    country = models.CharField(_("country"), max_length=120, blank=True, default="United States")

    # Normalized address key for duplicate detection (Phase 4).
    normalized_address = models.CharField(
        _("normalized address"), max_length=500, blank=True, editable=False, db_index=True
    )

    employee_count = models.PositiveIntegerField(_("employee count"), null=True, blank=True)

    source = models.CharField(_("source"), max_length=120, blank=True, db_index=True)

    class Meta:
        verbose_name = _("company")
        verbose_name_plural = _("companies")
        ordering = ("name", "id")
        indexes = (
            models.Index(fields=["state", "city"], name="company_state_city_idx"),
            models.Index(fields=["industry", "state"], name="company_industry_state_idx"),
            models.Index(fields=["normalized_name", "city", "state"], name="company_name_city_state_idx"),
            models.Index(fields=["normalized_phone"], name="company_norm_phone_idx"),
        )
        constraints = (
            # One record per domain. Blank domains stay out of the constraint so
            # companies without a website can coexist.
            models.UniqueConstraint(
                fields=["normalized_website"],
                condition=~Q(normalized_website=""),
                name="company_unique_normalized_website",
            ),
            models.CheckConstraint(
                condition=Q(employee_count__isnull=True) | Q(employee_count__gte=0),
                name="company_employee_count_non_negative",
            ),
        )

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        self.name = normalize_whitespace(self.name)
        self.normalized_name = normalize_company_name(self.name)
        self.normalized_website = normalize_domain(self.website)
        self.normalized_phone = normalize_phone(self.phone)

        for field in ("industry", "sub_industry", "city", "zip_code", "country", "source"):
            setattr(self, field, normalize_whitespace(getattr(self, field)))
        self.street_address = normalize_whitespace(self.street_address)
        # Normalize state abbreviation (e.g. "Ohio" -> "OH") when possible.
        self.state = normalize_state(self.state) if self.state else ""
        self.normalized_address = normalize_address(
            self.street_address, self.city, self.state, self.zip_code, self.country
        )

        super().save(*args, **kwargs)

    @property
    def domain(self) -> str:
        """Alias kept for readability in templates and the API."""
        return self.normalized_website

    @property
    def location(self) -> str:
        """``"Columbus, OH"`` — falls back gracefully when parts are missing."""
        return ", ".join(part for part in (self.city, self.state) if part)
