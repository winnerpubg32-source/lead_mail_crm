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
    """Every domain module must be routed — implemented or still a stub."""

    #: Modules with real endpoints (Phase 2) and the route that proves it.
    IMPLEMENTED_MODULES: tuple[tuple[str, str], ...] = (
        ("companies", "companies:company-list"),
        ("contacts", "contacts:contact-list"),
        ("leads", "leads:lead-list"),
    )

    #: Modules that are registered and routed but ship in a later phase.
    STUB_MODULES = (
        "imports",
        "campaigns",
        "email_engine",
        "ai_engine",
        "crm",
        "analytics",
        "suppression",
    )

    def test_implemented_modules_resolve_their_collection_route(self) -> None:
        for namespace, route in self.IMPLEMENTED_MODULES:
            with self.subTest(namespace=namespace):
                path = reverse(route)
                self.assertTrue(path.startswith(("/api/v1/", "/api/")))

    def test_unversioned_aliases_match_the_versioned_routes(self) -> None:
        """The brief uses /api/leads/; both spellings serve the same data."""
        for collection in ("companies", "contacts", "leads"):
            with self.subTest(collection=collection):
                versioned = self.client.get(f"/api/v1/{collection}/")
                unversioned = self.client.get(f"/api/{collection}/")
                self.assertEqual(versioned.status_code, 200)
                self.assertEqual(unversioned.status_code, 200)
                self.assertEqual(versioned.json(), unversioned.json())

    def test_unversioned_alias_serves_detail_and_search(self) -> None:
        from apps.companies.models import Company
        from apps.contacts.models import Contact
        from apps.leads.models import EmailStatus, Lead, LeadStatus

        company = Company.objects.create(name="Alias Test Co", industry="Software")
        contact = Contact.objects.create(
            company=company,
            first_name="Alias",
            last_name="Tester",
            email="alias@example.com",
        )
        lead = Lead.objects.create(
            company=company,
            contact=contact,
            lead_score=42,
            lead_status=LeadStatus.QUALIFIED,
            email_status=EmailStatus.VALID,
        )

        detail = self.client.get(f"/api/leads/{lead.pk}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["id"], lead.pk)
        self.assertEqual(detail.json()["lead_status"], "QUALIFIED")

        search = self.client.get("/api/leads/?search=Alias").json()
        self.assertEqual(search["count"], 1)
        self.assertEqual(search["results"][0]["company_name"], "Alias Test Co")

    def test_stub_modules_still_expose_a_status_route(self) -> None:
        for namespace in self.STUB_MODULES:
            with self.subTest(namespace=namespace):
                self.assertIsNotNone(reverse(f"{namespace}:ping"))

    def test_module_routes_are_reachable(self) -> None:
        for path in (
            "/api/v1/companies/",
            "/api/v1/contacts/",
            "/api/v1/leads/",
            "/api/v1/imports/",
            "/api/v1/suppression/",
            "/api/companies/",
            "/api/contacts/",
            "/api/leads/",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_health_reverse(self) -> None:
        self.assertEqual(reverse("core:health"), "/api/health/")
