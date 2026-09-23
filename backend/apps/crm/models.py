"""
CRM models — planned for a later phase.

This module is registered and routed in Phase 1 so the API surface and Django
app registry are already stable. No model is created yet: writing schema before
the import/outreach rules exist would force migrations we would immediately have
to rewrite.

Planned model fields:
  - stage : CharField(max_length=40, blank=True)
  - amount : DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
  - next_step_at : DateTimeField(null=True, blank=True)

Planned capabilities:
  - Deal model with stages and amounts
  - Notes + tasks attached to leads and contacts
  - Unified activity feed
"""

from __future__ import annotations

# Intentionally empty: models arrive with the CRM feature.
# When they do, inherit from core.models so timestamps and ownership stay
# consistent across the product:
#
#     from core.models import BaseModel, OwnedModel
#
# Planned: Deals, notes, tasks and the activity timeline behind every lead.
