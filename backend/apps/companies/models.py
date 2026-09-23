"""
Companies models — planned for a later phase.

This module is registered and routed in Phase 1 so the API surface and Django
app registry are already stable. No model is created yet: writing schema before
the import/outreach rules exist would force migrations we would immediately have
to rewrite.

Planned model fields:
  - name : CharField(max_length=255)
  - domain : SlugField(max_length=255, blank=True)
  - website : URLField(blank=True)
  - industry : CharField(max_length=150, blank=True)
  - city : CharField(max_length=120, blank=True)
  - state : CharField(max_length=120, blank=True)
  - country : CharField(max_length=120, blank=True, default='US')
  - employee_range : CharField(max_length=50, blank=True)

Planned capabilities:
  - Company model with normalised domain + industry taxonomy
  - Deduplication by domain name during import
  - Bulk endpoints for large datasets
"""

from __future__ import annotations

# Intentionally empty: models arrive with the Companies feature.
# When they do, inherit from core.models so timestamps and ownership stay
# consistent across the product:
#
#     from core.models import BaseModel, OwnedModel
#
# Planned: Imported businesses: name, website, industry, city, state, employee range.
