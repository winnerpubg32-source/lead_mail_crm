"""Routes for ``/api/v1/leads/``."""

from __future__ import annotations

from django.urls import path

from apps.leads import views

app_name = "leads"

urlpatterns = [
    path("", views.LeadsRootView.as_view(), name="ping"),
    # Later phases append their viewset routers below.
]
