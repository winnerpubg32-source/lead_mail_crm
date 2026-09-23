"""
Email engine background tasks — empty in Phase 1.

Celery is fully wired (broker, result backend, autodiscovery); this module only
declares where the Email engine tasks will live so ``celery worker`` picks them up
automatically once they exist.
"""

from __future__ import annotations

# from celery import shared_task  # enable in the Email engine phase
