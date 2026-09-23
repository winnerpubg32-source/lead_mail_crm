"""
Contacts models — planned for a later phase.

This module is registered and routed in Phase 1 so the API surface and Django
app registry are already stable. No model is created yet: writing schema before
the import/outreach rules exist would force migrations we would immediately have
to rewrite.

Planned model fields:
  - first_name : CharField(max_length=120, blank=True)
  - last_name : CharField(max_length=120, blank=True)
  - email : EmailField(blank=True)
  - phone : CharField(max_length=40, blank=True)
  - job_title : CharField(max_length=180, blank=True)
  - linkedin_url : URLField(blank=True)
  - email_status : CharField(max_length=20, blank=True)

Planned capabilities:
  - Contact model linked to Company and Lead
  - E-mail normalisation + validation status (valid / risky / invalid)
  - Role detection for decision-maker targeting
"""

from __future__ import annotations

# Intentionally empty: models arrive with the Contacts feature.
# When they do, inherit from core.models so timestamps and ownership stay
# consistent across the product:
#
#     from core.models import BaseModel, OwnedModel
#
# Planned: People attached to companies: name, job title, e-mail, phone, LinkedIn.
