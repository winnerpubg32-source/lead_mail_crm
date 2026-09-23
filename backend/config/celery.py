"""
Celery application for OutreachOS.

Phase 1 only wires the broker/result backend and task autodiscovery. Background
work queues (import processing, campaign execution, daily send limits) are
implemented in later phases.
"""

from __future__ import annotations

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("outreachos")

# Read every CELERY_* setting from Django's settings module.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks.py modules inside all installed apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> str:  # pragma: no cover - infrastructure smoke test
    """Trivial task used to verify that a worker is connected to the broker."""
    return f"worker ready: {self.request.hostname}"
