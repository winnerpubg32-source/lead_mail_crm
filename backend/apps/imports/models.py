"""
Imports models — planned for a later phase.

This module is registered and routed in Phase 1 so the API surface and Django
app registry are already stable. No model is created yet: writing schema before
the import/outreach rules exist would force migrations we would immediately have
to rewrite.

Planned model fields:
  - file_name : CharField(max_length=255, blank=True)
  - status : CharField(max_length=32, blank=True)
  - total_rows : IntegerField(default=0)
  - processed_rows : IntegerField(default=0)
  - failed_rows : IntegerField(default=0)

Planned capabilities:
  - Upload endpoint with column mapping
  - Celery chunked processing for large files
  - Row-level error reporting and rollback
"""

from __future__ import annotations

# Intentionally empty: models arrive with the Imports feature.
# When they do, inherit from core.models so timestamps and ownership stay
# consistent across the product:
#
#     from core.models import BaseModel, OwnedModel
#
# Planned: CSV/XLSX ingestion runs for large business datasets.
