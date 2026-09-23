"""API tests for ``/api/v1/companies/``."""

from __future__ import annotations

from django.test import TestCase
from rest_framework.test import APIClient

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.leads.models import Lead

LIST_URL = "/api/v1/companies/"


class CompanyApiTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.northwind = Company.objects.create(
            name="Northwind Logistics, Inc.",
            industry="Transportation & Logistics",
            city="Columbus",
            state="OH",
            website="https://www.northwindlogistics.com",
            phone="614-555-0100",
            employee_count=850,
            source="dataset_import",
        )
        cls.brightline = Company.objects.create(
            name="Brightline Dental Group",
            industry="Healthcare",
            city="Tampa",
            state="FL",
            website="brightlinedental.com",
            employee_count=120,
            source="website_form",
        )
        cls.no_site = Company.objects.create(name="Quiet Ledger LLC", state="OH", source="referral")

        contact = Contact.objects.create(company=cls.northwind, full_name="Marcus Whitfield")
        Lead.objects.create(company=cls.northwind, contact=contact, lead_status="QUALIFIED")

    def setUp(self) -> None:
        self.client = APIClient()

    def test_list_is_paginated_and_counts_relations(self) -> None:
        body = self.client.get(LIST_URL).json()
        self.assertEqual(body["count"], 3)

        northwind = next(
            row for row in body["results"] if row["name"] == "Northwind Logistics, Inc."
        )
        self.assertEqual(northwind["lead_count"], 1)
        self.assertEqual(northwind["contact_count"], 1)
        self.assertEqual(northwind["location"], "Columbus, OH")
        self.assertEqual(northwind["normalized_website"], "northwindlogistics.com")

    def test_detail_exposes_every_model_field(self) -> None:
        body = self.client.get(f"{LIST_URL}{self.northwind.pk}/").json()
        for field in (
            "id",
            "name",
            "normalized_name",
            "industry",
            "sub_industry",
            "website",
            "normalized_website",
            "phone",
            "normalized_phone",
            "street_address",
            "city",
            "state",
            "zip_code",
            "country",
            "employee_count",
            "source",
            "created_at",
            "updated_at",
        ):
            self.assertIn(field, body, f"missing field {field}")
        self.assertEqual(body["normalized_name"], "northwind logistics")

    def test_search_matches_name_domain_and_location(self) -> None:
        self.assertEqual(self.client.get(LIST_URL, {"search": "Northwind"}).json()["count"], 1)
        self.assertEqual(
            self.client.get(LIST_URL, {"search": "brightlinedental"}).json()["count"], 1
        )
        self.assertEqual(self.client.get(LIST_URL, {"search": "Tampa"}).json()["count"], 1)

    def test_filter_by_industry_state_and_source(self) -> None:
        self.assertEqual(self.client.get(LIST_URL, {"industry": "Healthcare"}).json()["count"], 1)
        self.assertEqual(self.client.get(LIST_URL, {"state": "OH"}).json()["count"], 2)
        self.assertEqual(self.client.get(LIST_URL, {"source": "referral"}).json()["count"], 1)

    def test_filter_by_employee_count_range(self) -> None:
        body = self.client.get(LIST_URL, {"employee_count_min": 200}).json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["name"], "Northwind Logistics, Inc.")

        body = self.client.get(
            LIST_URL, {"employee_count_min": 100, "employee_count_max": 200}
        ).json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["name"], "Brightline Dental Group")

    def test_filter_by_has_website(self) -> None:
        self.assertEqual(self.client.get(LIST_URL, {"has_website": "true"}).json()["count"], 2)
        self.assertEqual(self.client.get(LIST_URL, {"has_website": "false"}).json()["count"], 1)

    def test_ordering_by_name_and_employee_count(self) -> None:
        by_name = self.client.get(LIST_URL, {"ordering": "name"}).json()["results"]
        self.assertEqual(
            [row["name"] for row in by_name],
            ["Brightline Dental Group", "Northwind Logistics, Inc.", "Quiet Ledger LLC"],
        )

        by_size = self.client.get(LIST_URL, {"ordering": "-employee_count"}).json()["results"]
        self.assertEqual(by_size[0]["name"], "Northwind Logistics, Inc.")

    def test_ordering_by_lead_count(self) -> None:
        by_leads = self.client.get(LIST_URL, {"ordering": "-lead_count"}).json()["results"]
        self.assertEqual(by_leads[0]["name"], "Northwind Logistics, Inc.")

    def test_search_and_filter_combine_with_pagination(self) -> None:
        body = self.client.get(LIST_URL, {"state": "OH", "page_size": 1}).json()
        self.assertEqual(body["count"], 2)
        self.assertEqual(len(body["results"]), 1)
        self.assertIsNotNone(body["next"])

    def test_list_queries_are_bounded(self) -> None:
        with self.assertNumQueries(2):  # count + annotated page
            self.client.get(LIST_URL, {"ordering": "-lead_count"})

    def test_module_status_endpoint_reports_total(self) -> None:
        body = self.client.get("/api/v1/companies/status/").json()
        self.assertEqual(body["module"], "companies")
        self.assertEqual(body["total"], 3)
