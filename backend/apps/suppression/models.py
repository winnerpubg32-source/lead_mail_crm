"""
Suppression models — planned for a later phase.

This module is registered and routed in Phase 1 so the API surface and Django
app registry are already stable. No model is created yet: writing schema before
the import/outreach rules exist would force migrations we would immediately have
to rewrite.

Planned model fields:
  - email : EmailField(blank=True)
  - domain : CharField(max_length=255, blank=True)
  - reason : CharField(max_length=40, blank=True)
  - notes : TextField(blank=True)

Planned capabilities:
  - Suppression entries checked before every send
  - One-click unsubscribe endpoint
  - Imported suppression lists
"""

from __future__ import annotations

# Intentionally empty: models arrive with the Suppression feature.
# When they do, inherit from core.models so timestamps and ownership stay
# consistent across the product:
#
#     from core.models import BaseModel, OwnedModel
#
# Planned: Global do-not-contact list: unsubscribes, hard bounces, manual blocks.
