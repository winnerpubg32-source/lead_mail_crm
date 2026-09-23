"""API tests for ``/api/v1/contacts/``."""

from __future__ import annotations

from django.test import TestCase
from rest_framework.test import APIClient

from apps.companies.models import Company
from apps.contacts.models import Contact, PhoneType

LIST_URL = "/api/v1/contacts/"


class ContactApiTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.northwind = Company.objects.create(
            name="Northwind Logistics, Inc.",
            industry="Transportation & Logistics",
            city="Columbus",
            state="OH",
            source="dataset_import",
        )
        cls.brightline = Company.objects.create(
            name="Brightline Dental Group", industry="Healthcare", city="Tampa", state="FL"
        )

        cls.marcus = Contact.objects.create(
            company=cls.northwind,
            first_name="Marcus",
            last_name="Whitfield",
            job_title="VP Operations",
            email="M.Whitfield@NorthwindLogistics.com",
            phone="+1 (614) 555-0142",
            phone_type=PhoneType.MOBILE,
        )
        cls.elena = Contact.objects.create(
            company=cls.brightline,
            first_name="Elena",
            last_name="Ruiz",
            job_title="Managing Partner",
            email="elena.ruiz@brightlinedental.com",
        )
        cls.no_email = Contact.objects.create(company=cls.northwind, full_name="Front Desk")

    def setUp(self) -> None:
        self.client = APIClient()

    def test_list_is_paginated_and_includes_company_context(self) -> None:
        body = self.client.get(LIST_URL).json()
        self.assertEqual(body["count"], 3)

        marcus = next(row for row in body["results"] if row["full_name"] == "Marcus Whitfield")
        self.assertEqual(marcus["company_name"], "Northwind Logistics, Inc.")
        self.assertEqual(marcus["company_industry"], "Transportation & Logistics")
        self.assertEqual(marcus["company_city"], "Columbus")
        self.assertEqual(marcus["company_state"], "OH")
        self.assertEqual(marcus["email"], "m.whitfield@northwindlogistics.com")
        self.assertEqual(marcus["normalized_email"], "m.whitfield@northwindlogistics.com")
        self.assertEqual(marcus["normalized_phone"], "+16145550142")
        self.assertEqual(marcus["phone_type"], "MOBILE")

    def test_detail_exposes_every_model_field(self) -> None:
        body = self.client.get(f"{LIST_URL}{self.marcus.pk}/").json()
        for field in (
            "id",
            "company",
            "first_name",
            "last_name",
            "full_name",
            "job_title",
            "email",
            "normalized_email",
            "phone",
            "phone_type",
            "created_at",
            "updated_at",
        ):
            self.assertIn(field, body, f"missing field {field}")

    def test_search_by_name_title_and_email(self) -> None:
        self.assertEqual(self.client.get(LIST_URL, {"search": "Elena"}).json()["count"], 1)
        self.assertEqual(
            self.client.get(LIST_URL, {"search": "Managing Partner"}).json()["count"], 1
        )
        self.assertEqual(self.client.get(LIST_URL, {"search": "whitfield@"}).json()["count"], 1)
        # Company name is searchable from the contact list too.
        self.assertEqual(self.client.get(LIST_URL, {"search": "Brightline"}).json()["count"], 1)

    def test_filter_by_company_and_source(self) -> None:
        self.assertEqual(
            self.client.get(LIST_URL, {"company": str(self.northwind.pk)}).json()["count"], 2
        )
        self.assertEqual(self.client.get(LIST_URL, {"source": "dataset_import"}).json()["count"], 2)
        self.assertEqual(self.client.get(LIST_URL, {"source": "website_form"}).json()["count"], 0)

    def test_filter_by_location_and_industry_of_the_company(self) -> None:
        self.assertEqual(self.client.get(LIST_URL, {"state": "FL"}).json()["count"], 1)
        self.assertEqual(self.client.get(LIST_URL, {"city": "Columbus"}).json()["count"], 2)
        self.assertEqual(self.client.get(LIST_URL, {"industry": "Healthcare"}).json()["count"], 1)

    def test_filter_has_email(self) -> None:
        self.assertEqual(self.client.get(LIST_URL, {"has_email": "true"}).json()["count"], 2)
        self.assertEqual(self.client.get(LIST_URL, {"has_email": "false"}).json()["count"], 1)

    def test_filter_by_phone_type_and_job_title(self) -> None:
        self.assertEqual(self.client.get(LIST_URL, {"phone_type": "MOBILE"}).json()["count"], 1)
        self.assertEqual(self.client.get(LIST_URL, {"job_title": "partner"}).json()["count"], 1)

    def test_ordering_by_name_title_and_company(self) -> None:
        by_name = self.client.get(LIST_URL, {"ordering": "full_name"}).json()["results"]
        self.assertEqual(
            [row["full_name"] for row in by_name], ["Elena Ruiz", "Front Desk", "Marcus Whitfield"]
        )

        by_company = self.client.get(LIST_URL, {"ordering": "company__name"}).json()["results"]
        self.assertEqual(by_company[0]["company_name"], "Brightline Dental Group")

        by_title = self.client.get(LIST_URL, {"ordering": "job_title"}).json()["results"]
        self.assertEqual(by_title[0]["full_name"], "Front Desk")  # empty title sorts first

    def test_empty_result_set_returns_zero_count(self) -> None:
        body = self.client.get(LIST_URL, {"search": "no-such-person"}).json()
        self.assertEqual(body["count"], 0)
        self.assertEqual(body["results"], [])

    def test_list_queries_are_bounded(self) -> None:
        with self.assertNumQueries(2):  # count + page with select_related(company)
            self.client.get(LIST_URL)

    def test_module_status_endpoint_reports_total(self) -> None:
        body = self.client.get("/api/v1/contacts/status/").json()
        self.assertEqual(body["module"], "contacts")
        self.assertEqual(body["total"], 3)
