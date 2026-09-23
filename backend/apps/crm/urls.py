"""Routes for ``/api/v1/crm/``."""

from __future__ import annotations

from django.urls import path

from apps.crm import views

app_name = "crm"

urlpatterns = [
    path("", views.CrmRootView.as_view(), name="ping"),
    # Later phases append their viewset routers below.
]
