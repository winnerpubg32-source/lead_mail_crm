"""
Email engine models — planned for a later phase.

This module is registered and routed in Phase 1 so the API surface and Django
app registry are already stable. No model is created yet: writing schema before
the import/outreach rules exist would force migrations we would immediately have
to rewrite.

Planned model fields:
  - subject : CharField(max_length=255, blank=True)
  - status : CharField(max_length=32, blank=True)
  - sent_at : DateTimeField(null=True, blank=True)
  - error_message : TextField(blank=True)

Planned capabilities:
  - Daily send budget with Redis counter (max 90/day)
  - Per-mailbox SMTP configuration stored encrypted
  - Bounce/complaint handling and automatic suppression
"""

from __future__ import annotations

# Intentionally empty: models arrive with the Email engine feature.
# When they do, inherit from core.models so timestamps and ownership stay
# consistent across the product:
#
#     from core.models import BaseModel, OwnedModel
#
# Planned: SMTP delivery with a hard cap of 90 marketing e-mails per day.
