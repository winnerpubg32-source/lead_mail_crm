"""Routes for ``/api/v1/imports/``."""

from __future__ import annotations

from django.urls import path

from apps.imports import views

app_name = "imports"

urlpatterns = [
    path("", views.ImportsRootView.as_view(), name="ping"),
    # Later phases append their viewset routers below.
]
