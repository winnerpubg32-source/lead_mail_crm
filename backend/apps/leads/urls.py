"""Routes for ``/api/v1/leads/``."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.leads import views

app_name = "leads"

router = DefaultRouter()
router.register("", views.LeadViewSet, basename="lead")

urlpatterns = router.urls
