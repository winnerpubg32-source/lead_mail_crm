"""Infrastructure endpoints — mounted at ``/api/``."""

from __future__ import annotations

from django.urls import path

from core import views

app_name = "core"

urlpatterns = [
    path("", views.ApiRootView.as_view(), name="api-root"),
    path("health/", views.HealthView.as_view(), name="health"),
    path("ready/", views.ReadinessView.as_view(), name="ready"),
    path("version/", views.VersionView.as_view(), name="version"),
]
