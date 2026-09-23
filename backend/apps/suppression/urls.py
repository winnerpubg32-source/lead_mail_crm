"""Routes for ``/api/v1/suppression/``."""

from __future__ import annotations

from django.urls import path

from apps.suppression import views

app_name = "suppression"

urlpatterns = [
    path("", views.SuppressionRootView.as_view(), name="ping"),
    # Later phases append their viewset routers below.
]
