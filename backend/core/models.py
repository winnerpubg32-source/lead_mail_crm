"""
Abstract building blocks for every OutreachOS model.

Phase 1 has no domain models yet; later phases inherit from these so timestamps,
soft-delete semantics and ownership behave identically everywhere.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Adds ``created_at`` / ``updated_at`` to a model."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseModel(TimeStampedModel):
    """Timestamped model with a client supplied identifier (import friendly)."""

    public_id = models.UUIDField(editable=False, unique=True, null=True, blank=True)

    class Meta:
        abstract = True


class OwnedModel(BaseModel):
    """Model belonging to a user — the anchor for workspace scoping."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_set",
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True
