"""Routes for ``/api/v1/email/`` (Phase 6: templates; Phase 7: SMTP/sending)."""

from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.email_engine import views

app_name = "email_engine"

router = DefaultRouter()
router.register("templates", views.EmailTemplateViewSet, basename="email-template")

urlpatterns = [
    path("ping", views.EmailEnginePingView.as_view(), name="ping"),
    *router.urls,
]
