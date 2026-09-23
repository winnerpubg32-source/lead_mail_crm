"""
OutreachOS Django project package.

The Celery application is imported here so that ``@shared_task`` decorators are
bound to the same app instance when Django starts (this is the documented
Celery + Django integration pattern).
"""

from __future__ import annotations

from .celery import app as celery_app

__all__ = ("celery_app",)
