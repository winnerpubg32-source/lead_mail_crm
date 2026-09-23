"""Routes for ``/api/v1/contacts/``."""

from __future__ import annotations

from django.urls import path

from apps.contacts import views

app_name = "contacts"

urlpatterns = [
    path("", views.ContactsRootView.as_view(), name="ping"),
    # Later phases append their viewset routers below.
]
