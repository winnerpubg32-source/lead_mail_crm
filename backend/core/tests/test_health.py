"""Infrastructure endpoint tests (Phase 1 acceptance)."""

from __future__ import annotations

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient


class HealthEndpointTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_health_returns_ok(self) -> None:
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_health_is_unauthenticated(self) -> None:
        response = self.client.get("/api/health/")
        self.assertNotIn("detail", response.json())

    def test_version_endpoint_exposes_daily_limit(self) -> None:
        response = self.client.get("/api/version/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["daily_email_limit"], 90)

    def test_api_root_lists_endpoints(self) -> None:
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("health", response.json()["endpoints"])

    def test_ready_endpoint_reports_dependencies(self) -> None:
        response = self.client.get("/api/ready/")
        self.assertIn(response.status_code, (200, 503))
        self.assertIn("database", response.json()["dependencies"])

    @override_settings(OUTREACH_DAILY_EMAIL_LIMIT=90)
    def test_daily_limit_is_configurable(self) -> None:
        response = self.client.get("/api/version/")
        self.assertEqual(response.json()["daily_email_limit"], 90)

    def test_unknown_route_uses_error_envelope(self) -> None:
        response = self.client.get("/api/does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.json())


class UrlResolutionTests(TestCase):
    """Every domain module must already be routed (empty routers in Phase 1)."""

    def test_domain_module_namespaces_exist(self) -> None:
        for namespace in (
            "accounts",
            "companies",
            "contacts",
            "leads",
            "imports",
            "campaigns",
            "email_engine",
            "ai_engine",
            "crm",
            "analytics",
            "suppression",
        ):
            with self.subTest(namespace=namespace):
                self.assertIsNotNone(reverse(f"{namespace}:ping"))

    def test_health_reverse(self) -> None:
        self.assertEqual(reverse("core:health"), "/api/health/")
