"""
Leads models — planned for a later phase.

This module is registered and routed in Phase 1 so the API surface and Django
app registry are already stable. No model is created yet: writing schema before
the import/outreach rules exist would force migrations we would immediately have
to rewrite.

Planned model fields:
  - status : CharField(max_length=32, blank=True)
  - source : CharField(max_length=80, blank=True)
  - score : IntegerField(default=0)
  - qualified : BooleanField(default=False)
  - owner_note : TextField(blank=True)

Planned capabilities:
  - Lead model with status pipeline and qualification signals
  - Lead scoring inputs from the AI engine
  - Assignment / ownership rules
"""

from __future__ import annotations

# Intentionally empty: models arrive with the Leads feature.
# When they do, inherit from core.models so timestamps and ownership stay
# consistent across the product:
#
#     from core.models import BaseModel, OwnedModel
#
# Planned: Prospects moving through qualification and the outreach pipeline.
