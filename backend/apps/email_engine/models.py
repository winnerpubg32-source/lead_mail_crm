"""
E-mail templates (Phase 6).

Phase 6 only implements template authoring + variable substitution + preview.
Phase 7 wires these to SMTP through the sending engine.
"""

from __future__ import annotations

import re
from typing import Any

from django.core.validators import MinLengthValidator
from django.db import models

from core.models import TimeStampedModel

__all__ = ["EmailTemplate", "TEMPLATE_VARIABLES", "render_template"]


# Variables supported by the template engine. Values must match the exact
# spelling of the keys expected by the UI so validation errors are actionable.
TEMPLATE_VARIABLES = [
    "first_name",
    "contact_name",
    "company_name",
    "industry",
    "city",
    "state",
    "website",
    "recommended_service",
]

_VAR_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")

SAMPLE_LEAD: dict[str, str] = {
    "first_name": "Alex",
    "contact_name": "Alex Morgan",
    "company_name": "Northwind Logistics, Inc.",
    "industry": "Transportation & Logistics",
    "city": "Columbus",
    "state": "OH",
    "website": "https://northwindlogistics.com",
    "recommended_service": "Freight Optimization Review",
}


class EmailTemplate(TimeStampedModel):
    """Reusable outbound e-mail template with subject + body."""

    name = models.CharField(max_length=180, validators=[MinLengthValidator(2)])
    description = models.TextField(blank=True, default="")
    subject = models.CharField(max_length=255, validators=[MinLengthValidator(3)])
    body = models.TextField(validators=[MinLengthValidator(10)])

    # Optional default for campaigns that don't override the service.
    default_recommended_service = models.CharField(max_length=180, blank=True, default="")

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def used_variables(self) -> list[str]:
        """Variables present in subject+body, in first-use order (deduped)."""
        seen: set[str] = set()
        out: list[str] = []
        for source in (self.subject, self.body):
            for match in _VAR_PATTERN.finditer(source):
                name = match.group(1)
                if name not in seen:
                    seen.add(name)
                    out.append(name)
        return out

    def unknown_variables(self) -> list[str]:
        """Variables present in the template but not in the supported list."""
        allowed = set(TEMPLATE_VARIABLES)
        return [name for name in self.used_variables() if name not in allowed]

    def missing_variables(self) -> list[str]:
        """Supported variables that the template does NOT reference (informational)."""
        used = set(self.used_variables())
        return [name for name in TEMPLATE_VARIABLES if name not in used]

    def render_preview(self, context: dict[str, Any] | None = None) -> dict[str, str]:
        """Render subject + body against a sample context (defaults to SAMPLE_LEAD)."""
        ctx = {**SAMPLE_LEAD, **(context or {})}
        return {
            "subject": render_template(self.subject, ctx),
            "body": render_template(self.body, ctx),
        }


def render_template(template: str, context: dict[str, Any]) -> str:
    """
    Replace ``{{ var }}`` placeholders with ``context[var]``.

    Unknown variables are replaced with an empty string so rendering never
    raises — editors see the hole disappear instead of crashing. ``{{`` / ``}}``
    inside plain text is safe because we match balanced braces only.
    """

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        value = context.get(name, "")
        return "" if value is None else str(value)

    return _VAR_PATTERN.sub(replace, template)
