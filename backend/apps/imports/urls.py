"""Routes for ``/api/v1/imports/``.

The viewset is registered at the router root so the collection lives at
``/api/v1/imports/`` and actions hang off it (``/upload/``, ``/fields/``,
``/status/``, ``/{id}/start/`` …). The same urlconf is mounted unversioned as
``/api/imports/`` in ``config/api_urls.py``.
"""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.imports import views

app_name = "imports"

router = DefaultRouter()
router.register("", views.ImportJobViewSet, basename="importjob")

urlpatterns = router.urls
