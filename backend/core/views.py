"""
Infrastructure views: API root, health, readiness and version.

These endpoints are intentionally free of business logic — they only report
whether the Django project, its database, Redis and the Celery broker are
reachable.
"""

from __future__ import annotations

import time

import django
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.serializers import HealthSerializer, ReadinessSerializer

SERVICE_NAME = "outreachos-api"
API_VERSION = "0.1.0"


class ApiRootView(APIView):
    """Discovery endpoint — lists what the API exposes in this phase."""

    @extend_schema(responses={200: None}, summary="API root")
    def get(self, request):
        return Response(
            {
                "service": settings.APP_NAME,
                "version": API_VERSION,
                "environment": settings.ENVIRONMENT,
                "endpoints": {
                    "health": request.build_absolute_uri("health/"),
                    "ready": request.build_absolute_uri("ready/"),
                    "version": request.build_absolute_uri("version/"),
                    "auth": request.build_absolute_uri("v1/accounts/"),
                },
                "phase": 1,
                "note": "Foundation only — outreach, imports, AI and CRM land in later phases.",
            }
        )


class HealthView(APIView):
    """Liveness probe.

    ``GET /api/health/`` -> ``{"status": "ok"}``
    """

    authentication_classes: tuple = ()
    permission_classes: tuple = ()

    @extend_schema(responses={200: HealthSerializer}, summary="Health check")
    def get(self, request):
        return Response(
            {
                "status": "ok",
                "service": SERVICE_NAME,
                "version": API_VERSION,
                "environment": settings.ENVIRONMENT,
                "time": timezone.now(),
            }
        )


class ReadinessView(APIView):
    """Readiness probe — checks the dependencies the app needs to serve traffic."""

    authentication_classes: tuple = ()
    permission_classes: tuple = ()

    @extend_schema(
        responses={200: ReadinessSerializer, 503: ReadinessSerializer}, summary="Readiness check"
    )
    def get(self, request):
        started = time.perf_counter()
        dependencies = {
            "database": self._check_database(),
            "cache": self._check_cache(),
            "broker": self._check_broker(),
        }
        healthy = all(value == "ok" for value in dependencies.values())
        payload = {
            "status": "ok" if healthy else "degraded",
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "dependencies": dependencies,
        }
        code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(payload, status=code)

    # -- dependency probes --------------------------------------------------
    @staticmethod
    def _check_database() -> str:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
            return "ok"
        except Exception as exc:  # pragma: no cover - depends on environment
            return f"error: {exc.__class__.__name__}"

    @staticmethod
    def _check_cache() -> str:
        try:
            cache.set("outreachos:health", "1", 5)
            return "ok" if cache.get("outreachos:health") == "1" else "error: unavailable"
        except Exception as exc:  # pragma: no cover - depends on environment
            return f"error: {exc.__class__.__name__}"

    @staticmethod
    def _check_broker() -> str:
        """Ping Redis (the Celery broker) without importing a worker."""
        try:
            import redis  # imported lazily: Redis is optional in bare setups

            client = redis.Redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=2)
            client.ping()
            return "ok"
        except Exception as exc:  # pragma: no cover - depends on environment
            return f"error: {exc.__class__.__name__}"


class VersionView(APIView):
    """Build/version metadata used by the dashboard footer and CI."""

    authentication_classes: tuple = ()
    permission_classes: tuple = ()

    @extend_schema(responses={200: None}, summary="Version")
    def get(self, request):
        return Response(
            {
                "service": SERVICE_NAME,
                "application": settings.APP_NAME,
                "version": API_VERSION,
                "environment": settings.ENVIRONMENT,
                "django": django.get_version(),
                "daily_email_limit": settings.OUTREACH_DAILY_EMAIL_LIMIT,
            }
        )
