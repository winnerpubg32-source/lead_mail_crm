"""Routes for ``/api/v1/ai-engine/``."""

from __future__ import annotations

from django.urls import path

from apps.ai_engine import views

app_name = "ai_engine"

urlpatterns = [
    path("", views.AiEngineRootView.as_view(), name="ping"),
    # Later phases append their viewset routers below.
]
