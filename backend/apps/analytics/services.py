"""
Domain services for the Analytics module.

Views stay thin; business rules live here so they can be reused by Celery
tasks, management commands and the API alike. Empty in Phase 1.
"""

from __future__ import annotations
