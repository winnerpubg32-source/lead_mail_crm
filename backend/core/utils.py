"""Small helpers shared across the foundation."""

from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings


def build_absolute_url(request: Any, path: str) -> str:
    """Return an absolute URL for a request-relative path."""
    if request is None:
        return path
    return request.build_absolute_uri(path)


def new_public_id() -> uuid.UUID:
    """Generate an identifier clients can safely reference (never the PK)."""
    return uuid.uuid4()


def daily_email_capacity() -> dict[str, int]:
    """Single source of truth for the 90 e-mails/day policy."""
    limit = int(getattr(settings, "OUTREACH_DAILY_EMAIL_LIMIT", 90))
    return {"limit": limit}
