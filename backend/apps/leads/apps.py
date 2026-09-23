from __future__ import annotations

from django.apps import AppConfig


class LeadsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.leads"
    label = "leads"
    verbose_name = "Leads"

    def ready(self):
        # Register post_save signal that scores newly-created leads.
        from . import signals  # noqa: F401
