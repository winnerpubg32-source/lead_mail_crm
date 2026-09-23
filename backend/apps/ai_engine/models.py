"""
AI engine models — planned for a later phase.

This module is registered and routed in Phase 1 so the API surface and Django
app registry are already stable. No model is created yet: writing schema before
the import/outreach rules exist would force migrations we would immediately have
to rewrite.

Planned model fields:
  - provider : CharField(max_length=40, blank=True)
  - model_name : CharField(max_length=80, blank=True)
  - prompt : TextField(blank=True)
  - output : TextField(blank=True)
  - tokens_used : IntegerField(default=0)

Planned capabilities:
  - Provider abstraction (OpenAI / Anthropic / local)
  - Prompt templates with brand voice controls
  - Cost + token accounting per generation
"""

from __future__ import annotations

# Intentionally empty: models arrive with the AI engine feature.
# When they do, inherit from core.models so timestamps and ownership stay
# consistent across the product:
#
#     from core.models import BaseModel, OwnedModel
#
# Planned: Lead qualification and personalised B2B outreach copy generation.
