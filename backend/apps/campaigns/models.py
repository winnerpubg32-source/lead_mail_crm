"""
Campaigns models — planned for a later phase.

This module is registered and routed in Phase 1 so the API surface and Django
app registry are already stable. No model is created yet: writing schema before
the import/outreach rules exist would force migrations we would immediately have
to rewrite.

Planned model fields:
  - name : CharField(max_length=180, blank=True)
  - status : CharField(max_length=32, blank=True)
  - daily_limit : IntegerField(default=90)
  - starts_at : DateTimeField(null=True, blank=True)
  - ends_at : DateTimeField(null=True, blank=True)

Planned capabilities:
  - Campaign + CampaignStep models
  - Audience builder on top of leads
  - Execution orchestration wired to the e-mail engine
"""

from __future__ import annotations

# Intentionally empty: models arrive with the Campaigns feature.
# When they do, inherit from core.models so timestamps and ownership stay
# consistent across the product:
#
#     from core.models import BaseModel, OwnedModel
#
# Planned: Outreach sequences: audience, steps, schedule and sending window.
