"""Reusable permission classes.

Phase 1 keeps the API open (``AllowAny`` in settings) so the dashboard can be
built against live endpoints. ``IsOwner`` and ``ReadOnly`` are already in place
because every domain model added later will start from them.
"""

from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission


class ReadOnly(BasePermission):
    """Allow safe HTTP methods only."""

    def has_permission(self, request, view) -> bool:
        return request.method in SAFE_METHODS


class IsOwner(BasePermission):
    """Object-level check for the ``owner`` convention used across the domain."""

    def has_object_permission(self, request, view, obj) -> bool:
        owner = getattr(obj, "owner", None) or getattr(obj, "user", None)
        return owner is None or owner == request.user
