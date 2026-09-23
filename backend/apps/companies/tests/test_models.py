"""Company model tests — normalisation on save and database constraints."""

from __future__ import annotations

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.companies.models import Company
from core.normalization import normalize_company_name


class CompanyModelTests(TestCase):
    def test_save_derives_normalized_fields(self) -> None:
        company = Company.objects.create(
            name="  Northwind Logistics, Inc. ",
            website="https://www.NorthwindLogistics.com/about",
            phone="(614) 555-0142",
            city=" Columbus ",
            state=" OH ",
            industry=" Transportation & Logistics ",
        )

        self.assertEqual(company.name, "Northwind Logistics, Inc.")
        self.assertEqual(company.normalized_name, "northwind logistics")
        self.assertEqual(company.normalized_website, "northwindlogistics.com")
        self.assertEqual(company.normalized_phone, "6145550142")
        self.assertEqual(company.city, "Columbus")
        self.assertEqual(company.state, "OH")
        self.assertEqual(company.industry, "Transportation & Logistics")

    def test_location_property_handles_partial_data(self) -> None:
        self.assertEqual(Company(name="A", city="Denver", state="CO").location, "Denver, CO")
        self.assertEqual(Company(name="A", state="CO").location, "CO")
        self.assertEqual(Company(name="A").location, "")

    def test_duplicate_domain_is_rejected(self) -> None:
        Company.objects.create(name="Acme One", website="acme.com")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Company.objects.create(name="Acme Two", website="https://www.acme.com/contact")

    def test_companies_without_website_can_share_empty_domain(self) -> None:
        Company.objects.create(name="No Site One")
        Company.objects.create(name="No Site Two")
        self.assertEqual(Company.objects.filter(normalized_website="").count(), 2)

    def test_normalized_name_is_updated_on_resave(self) -> None:
        company = Company.objects.create(name="Acme LLC")
        self.assertEqual(company.normalized_name, "acme")

        company.name = "Northwind Traders Ltd."
        company.save()
        company.refresh_from_db()
        self.assertEqual(company.normalized_name, "northwind traders")

    def test_legal_suffixes_do_not_change_the_matching_key(self) -> None:
        # Every variant of the same business must share one matching key.
        variants = ["Acme Holdings", "Acme Group", "Acme Inc.", "ACME, LLC", "acme corporation"]
        keys = {normalize_company_name(name) for name in variants}
        self.assertEqual(keys, {"acme"})

    def test_str_returns_name(self) -> None:
        self.assertEqual(str(Company(name="Brightline Dental")), "Brightline Dental")
