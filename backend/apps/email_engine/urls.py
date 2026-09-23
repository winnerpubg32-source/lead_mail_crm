"""Routes for ``/api/v1/email-engine/``."""

from __future__ import annotations

from django.urls import path

from apps.email_engine import views

app_name = "email_engine"

urlpatterns = [
    path("", views.EmailEngineRootView.as_view(), name="ping"),
    # Later phases append their viewset routers below.
]
