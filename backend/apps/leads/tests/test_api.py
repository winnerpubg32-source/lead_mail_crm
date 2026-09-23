"""API tests for ``/api/v1/leads/`` — pagination, search, filtering, ordering."""

from __future__ import annotations

from django.test import TestCase
from rest_framework.test import APIClient

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.leads.models import EmailStatus, Lead, LeadStatus

LIST_URL = "/api/v1/leads/"


class LeadApiTests(TestCase):
    """A small, deterministic dataset: 3 companies, 3 leads."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.northwind = Company.objects.create(
            name="Northwind Logistics, Inc.",
            industry="Transportation & Logistics",
            city="Columbus",
            state="OH",
            website="https://northwindlogistics.com",
            source="dataset_import",
        )
        cls.brightline = Company.objects.create(
            name="Brightline Dental Group",
            industry="Healthcare",
            city="Tampa",
            state="FL",
            source="website_form",
        )
        cls.vertex = Company.objects.create(
            name="Vertex Precision Manufacturing",
            industry="Manufacturing",
            city="Grand Rapids",
            state="MI",
            source="dataset_import",
        )

        cls.marcus = Contact.objects.create(
            company=cls.northwind,
            first_name="Marcus",
            last_name="Whitfield",
            job_title="VP Operations",
            email="m.whitfield@northwindlogistics.com",
            phone="614-555-0142",
        )
        cls.elena = Contact.objects.create(
            company=cls.brightline,
            first_name="Elena",
            last_name="Ruiz",
            job_title="Managing Partner",
            email="elena.ruiz@brightlinedental.com",
        )
        cls.dale = Contact.objects.create(
            company=cls.vertex,
            first_name="Dale",
            last_name="Kowalski",
            job_title="Plant Director",
            email="dkowalski@vertexprecision.com",
        )

        cls.lead_northwind = Lead.objects.create(
            company=cls.northwind,
            contact=cls.marcus,
            lead_score=92,
            lead_status=LeadStatus.QUALIFIED,
            email_status=EmailStatus.VALID,
            source="dataset_import",
            source_file="us_businesses_q3.csv",
            source_row_number=4287,
        )
        cls.lead_brightline = Lead.objects.create(
            company=cls.brightline,
            contact=cls.elena,
            lead_score=61,
            lead_status=LeadStatus.NEW,
            email_status=EmailStatus.UNKNOWN,
            source="website_form",
        )
        cls.lead_vertex = Lead.objects.create(
            company=cls.vertex,
            contact=cls.dale,
            lead_score=78,
            lead_status=LeadStatus.REPLIED,
            email_status=EmailStatus.UNSUBSCRIBED,
            source="dataset_import",
        )

    def setUp(self) -> None:
        self.client = APIClient()

    # -- response shape -----------------------------------------------------
    def test_list_is_paginated_with_count_next_previous_results(self) -> None:
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertEqual(set(body), {"count", "next", "previous", "results"})
        self.assertEqual(body["count"], 3)
        self.assertEqual(len(body["results"]), 3)
        self.assertIsNone(body["next"])
        self.assertIsNone(body["previous"])

        first = body["results"][0]
        # Every column the dashboard table needs is present.
        for field in (
            "id",
            "company",
            "company_name",
            "contact",
            "contact_name",
            "job_title",
            "email",
            "phone",
            "industry",
            "city",
            "state",
            "lead_score",
            "lead_status",
            "email_status",
        ):
            self.assertIn(field, first, f"missing field {field}")

    def test_detail_returns_the_lead(self) -> None:
        response = self.client.get(f"{LIST_URL}{self.lead_northwind.pk}/")
        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertEqual(body["id"], self.lead_northwind.pk)
        self.assertEqual(body["company_name"], "Northwind Logistics, Inc.")
        self.assertEqual(body["contact_name"], "Marcus Whitfield")
        self.assertEqual(body["job_title"], "VP Operations")
        self.assertEqual(body["email"], "m.whitfield@northwindlogistics.com")
        self.assertEqual(body["phone"], "614-555-0142")
        self.assertEqual(body["industry"], "Transportation & Logistics")
        self.assertEqual(body["city"], "Columbus")
        self.assertEqual(body["state"], "OH")
        self.assertEqual(body["lead_score"], 92)
        self.assertEqual(body["lead_status"], "QUALIFIED")
        self.assertEqual(body["email_status"], "VALID")
        self.assertEqual(body["source_file"], "us_businesses_q3.csv")
        self.assertEqual(body["source_row_number"], 4287)
        self.assertTrue(body["is_contactable"])

    def test_detail_404_uses_error_envelope(self) -> None:
        response = self.client.get(f"{LIST_URL}999999/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "not_found")

    # -- pagination ---------------------------------------------------------
    def test_page_size_and_pages(self) -> None:
        response = self.client.get(LIST_URL, {"page_size": 2})
        body = response.json()
        self.assertEqual(len(body["results"]), 2)
        self.assertIsNotNone(body["next"])

        second = self.client.get(LIST_URL, {"page_size": 2, "page": 2}).json()
        self.assertEqual(len(second["results"]), 1)
        self.assertIsNotNone(second["previous"])

    def test_page_size_is_capped(self) -> None:
        response = self.client.get(LIST_URL, {"page_size": 5000})
        self.assertEqual(response.status_code, 200)  # falls back to the max page size

    # -- search -------------------------------------------------------------
    def test_search_by_company_name(self) -> None:
        body = self.client.get(LIST_URL, {"search": "Northwind"}).json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["company_name"], "Northwind Logistics, Inc.")

    def test_search_by_contact_name_and_email(self) -> None:
        self.assertEqual(self.client.get(LIST_URL, {"search": "Elena"}).json()["count"], 1)
        self.assertEqual(
            self.client.get(LIST_URL, {"search": "vertexprecision"}).json()["count"], 1
        )

    def test_search_by_job_title(self) -> None:
        body = self.client.get(LIST_URL, {"search": "Plant Director"}).json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["contact_name"], "Dale Kowalski")

    def test_search_without_matches_returns_empty_results(self) -> None:
        body = self.client.get(LIST_URL, {"search": "zzzz-no-such-company"}).json()
        self.assertEqual(body["count"], 0)
        self.assertEqual(body["results"], [])

    # -- filtering ----------------------------------------------------------
    def test_filter_by_single_status(self) -> None:
        body = self.client.get(LIST_URL, {"lead_status": "QUALIFIED"}).json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["lead_status"], "QUALIFIED")

    def test_filter_by_multiple_statuses(self) -> None:
        body = self.client.get(LIST_URL, {"lead_status": ["QUALIFIED", "REPLIED"]}).json()
        self.assertEqual(body["count"], 2)

    def test_filter_by_comma_separated_statuses(self) -> None:
        body = self.client.get(LIST_URL, {"lead_status": "QUALIFIED,REPLIED"}).json()
        self.assertEqual(body["count"], 2)

    def test_filter_by_email_status(self) -> None:
        body = self.client.get(LIST_URL, {"email_status": "UNSUBSCRIBED"}).json()
        self.assertEqual(body["count"], 1)
        self.assertFalse(body["results"][0]["is_contactable"])

    def test_filter_by_industry_city_and_state(self) -> None:
        self.assertEqual(self.client.get(LIST_URL, {"industry": "Healthcare"}).json()["count"], 1)
        self.assertEqual(self.client.get(LIST_URL, {"city": "Columbus"}).json()["count"], 1)
        self.assertEqual(self.client.get(LIST_URL, {"state": "FL"}).json()["count"], 1)

    def test_filter_by_score_range(self) -> None:
        body = self.client.get(LIST_URL, {"min_score": 70}).json()
        self.assertEqual(body["count"], 2)
        body = self.client.get(LIST_URL, {"min_score": 70, "max_score": 80}).json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["contact_name"], "Dale Kowalski")

    def test_filter_by_source(self) -> None:
        self.assertEqual(self.client.get(LIST_URL, {"source": "dataset_import"}).json()["count"], 2)

    def test_filter_is_contactable(self) -> None:
        body = self.client.get(LIST_URL, {"is_contactable": "true"}).json()
        self.assertEqual(body["count"], 2)
        body = self.client.get(LIST_URL, {"is_contactable": "false"}).json()
        self.assertEqual(body["count"], 1)

    def test_filters_combine(self) -> None:
        body = self.client.get(LIST_URL, {"source": "dataset_import", "min_score": 80}).json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["company_name"], "Northwind Logistics, Inc.")

    def test_invalid_filter_value_returns_400(self) -> None:
        response = self.client.get(LIST_URL, {"lead_status": "NOT_A_STATUS"})
        self.assertEqual(response.status_code, 400)

    # -- ordering -----------------------------------------------------------
    def test_ordering_by_lead_score(self) -> None:
        ascending = self.client.get(LIST_URL, {"ordering": "lead_score"}).json()["results"]
        self.assertEqual([row["lead_score"] for row in ascending], [61, 78, 92])

        descending = self.client.get(LIST_URL, {"ordering": "-lead_score"}).json()["results"]
        self.assertEqual([row["lead_score"] for row in descending], [92, 78, 61])

    def test_ordering_by_company_and_contact_name(self) -> None:
        by_company = self.client.get(LIST_URL, {"ordering": "company__name"}).json()["results"]
        self.assertEqual(
            [row["company_name"] for row in by_company],
            [
                "Brightline Dental Group",
                "Northwind Logistics, Inc.",
                "Vertex Precision Manufacturing",
            ],
        )

        by_contact = self.client.get(LIST_URL, {"ordering": "contact__full_name"}).json()["results"]
        self.assertEqual(
            [row["contact_name"] for row in by_contact],
            ["Dale Kowalski", "Elena Ruiz", "Marcus Whitfield"],
        )

    def test_ordering_defaults_to_score_then_recency(self) -> None:
        results = self.client.get(LIST_URL).json()["results"]
        self.assertEqual(results[0]["lead_score"], 92)

    def test_ordering_by_unknown_field_falls_back_to_default(self) -> None:
        response = self.client.get(LIST_URL, {"ordering": "password"})
        self.assertEqual(response.status_code, 200)

    # -- status vocabulary --------------------------------------------------
    def test_statuses_endpoint_lists_enums_with_counts(self) -> None:
        response = self.client.get(f"{LIST_URL}statuses/")
        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertEqual(body["total"], 3)
        self.assertEqual(len(body["lead_status"]), 10)
        self.assertEqual(len(body["email_status"]), 6)

        qualified = next(item for item in body["lead_status"] if item["value"] == "QUALIFIED")
        self.assertEqual(qualified["label"], "Qualified")
        self.assertEqual(qualified["count"], 1)

        new_status = next(item for item in body["lead_status"] if item["value"] == "NEW")
        self.assertEqual(new_status["count"], 1)

    # -- queryset efficiency ------------------------------------------------
    def test_list_does_not_issue_n_plus_one_queries(self) -> None:
        # Exactly two queries regardless of row count: the page count and the
        # page itself — the join to company/contact happens in SQL, not per row.
        with self.assertNumQueries(2):
            self.client.get(LIST_URL, {"ordering": "company__name"})
