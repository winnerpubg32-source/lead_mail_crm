"""Routes for ``/api/v1/email/`` (templates, queue, and daily usage)."""

from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.email_engine import views

app_name = "email_engine"

router = DefaultRouter()
router.register("templates", views.EmailTemplateViewSet, basename="email-template")
router.register("messages", views.EmailMessageViewSet, basename="email-message")

urlpatterns = [
    path("ping", views.EmailEnginePingView.as_view(), name="ping"),
    path("usage/", views.EmailUsageView.as_view(), name="usage"),
    *router.urls,
]
