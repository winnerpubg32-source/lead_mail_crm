"""Routes for ``/api/v1/companies/``."""

from __future__ import annotations

from django.urls import path

from apps.companies import views

app_name = "companies"

urlpatterns = [
    path("", views.CompaniesRootView.as_view(), name="ping"),
    # Later phases append their viewset routers below.
]
