"""Routes for ``/api/v1/campaigns/`` (Phase 6)."""

from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.campaigns import views

app_name = "campaigns"

router = DefaultRouter()
router.register("", views.CampaignViewSet, basename="campaign")

urlpatterns = [
    # Backward-compat alias referenced by core health checks.
    path("ping", views.CampaignsPingView.as_view(), name="ping"),
    *router.urls,
]
