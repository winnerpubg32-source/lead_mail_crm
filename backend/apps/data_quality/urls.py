"""Routes for ``/api/v1/data-quality/``."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.data_quality import views

app_name = "data_quality"

router = DefaultRouter()
router.register("duplicates", views.DuplicateGroupViewSet, basename="duplicate")
router.register("missing-email", views.MissingEmailViewSet, basename="missing-email")
router.register("merges", views.MergeAuditViewSet, basename="merge-audit")

urlpatterns = [
    path("", views.DataQualityRootView.as_view(), name="ping"),
    path("stats/", views.DataQualityStatsView.as_view(), name="stats"),
    path("backfill/", views.BackfillView.as_view(), name="backfill"),
    path("", include(router.urls)),
]
