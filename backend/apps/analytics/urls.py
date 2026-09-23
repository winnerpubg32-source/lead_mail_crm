"""Routes for ``/api/v1/analytics/``."""

from __future__ import annotations

from django.urls import path

from apps.analytics import views

app_name = "analytics"

urlpatterns = [
    path("", views.AnalyticsRootView.as_view(), name="ping"),
    # Later phases append their viewset routers below.
]
