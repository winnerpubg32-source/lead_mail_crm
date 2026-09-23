"""Routes for ``/api/v1/contacts/``.

The collection lives at the bare path (``GET /api/v1/contacts/``) and detail
endpoints at ``/api/v1/contacts/{id}/``; ``/status/`` is a module summary.
"""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.contacts import views

app_name = "contacts"

router = DefaultRouter()
router.register("", views.ContactViewSet, basename="contact")

urlpatterns = router.urls
