"""Routes for ``/api/v1/companies/``.

The collection lives at the bare path (``GET /api/v1/companies/``) and detail
endpoints at ``/api/v1/companies/{id}/``; ``/status/`` is a module summary.
"""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.companies import views

app_name = "companies"

router = DefaultRouter()
router.register("", views.CompanyViewSet, basename="company")

urlpatterns = router.urls
