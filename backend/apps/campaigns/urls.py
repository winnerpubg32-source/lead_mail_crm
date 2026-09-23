"""Routes for ``/api/v1/campaigns/``."""

from __future__ import annotations

from django.urls import path

from apps.campaigns import views

app_name = "campaigns"

urlpatterns = [
    path("", views.CampaignsRootView.as_view(), name="ping"),
    # Later phases append their viewset routers below.
]
