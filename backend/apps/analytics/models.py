"""
Analytics models — planned for a later phase.

This module is registered and routed in Phase 1 so the API surface and Django
app registry are already stable. No model is created yet: writing schema before
the import/outreach rules exist would force migrations we would immediately have
to rewrite.

Planned model fields:
  - metric : CharField(max_length=80, blank=True)
  - value : DecimalField(max_digits=14, decimal_places=2, default=0)
  - period_start : DateField(null=True, blank=True)
  - period_end : DateField(null=True, blank=True)

Planned capabilities:
  - Nightly aggregation into metric tables
  - KPI endpoints for the dashboard cards
  - Source and campaign performance breakdowns
"""

from __future__ import annotations

# Intentionally empty: models arrive with the Analytics feature.
# When they do, inherit from core.models so timestamps and ownership stay
# consistent across the product:
#
#     from core.models import BaseModel, OwnedModel
#
# Planned: Aggregated reporting: outreach volume, replies, meetings, pipeline value.
