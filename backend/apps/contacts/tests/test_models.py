"""Contact model tests — name/e-mail normalisation and uniqueness."""

from __future__ import annotations

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.companies.models import Company
from apps.contacts.models import Contact, PhoneType


class ContactModelTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name="Northwind Logistics, Inc.")

    def test_save_builds_full_name_from_parts(self) -> None:
        contact = Contact.objects.create(company=self.company, first_name="Elena", last_name="Ruiz")
        self.assertEqual(contact.full_name, "Elena Ruiz")
        self.assertEqual(str(contact), "Elena Ruiz")

    def test_explicit_full_name_wins(self) -> None:
        contact = Contact.objects.create(
            company=self.company, first_name="Elena", last_name="Ruiz", full_name="Dr. Elena Ruiz"
        )
        self.assertEqual(contact.full_name, "Dr. Elena Ruiz")

    def test_normalizes_email_and_phone(self) -> None:
        contact = Contact.objects.create(
            company=self.company,
            first_name="Marcus",
            last_name="Whitfield",
            email="  M.Whitfield@NorthwindLogistics.COM ",
            phone="+1 (614) 555-0142",
            phone_type=PhoneType.MOBILE,
        )
        self.assertEqual(contact.email, "m.whitfield@northwindlogistics.com")
        self.assertEqual(contact.normalized_email, "m.whitfield@northwindlogistics.com")
        self.assertEqual(contact.normalized_phone, "+16145550142")
        self.assertTrue(contact.has_email)

    def test_duplicate_email_per_company_is_rejected(self) -> None:
        Contact.objects.create(company=self.company, full_name="A", email="info@acme.com")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Contact.objects.create(company=self.company, full_name="B", email="INFO@acme.com")

    def test_same_email_is_allowed_at_different_companies(self) -> None:
        other = Company.objects.create(name="Brightline Dental Group", website="brightline.com")
        Contact.objects.create(company=self.company, full_name="A", email="info@example.com")
        Contact.objects.create(company=other, full_name="B", email="info@example.com")
        self.assertEqual(Contact.objects.filter(normalized_email="info@example.com").count(), 2)

    def test_contact_can_exist_without_a_company(self) -> None:
        contact = Contact.objects.create(full_name="Unassigned Person", email="nobody@example.com")
        self.assertIsNone(contact.company_id)
        self.assertEqual(contact.company_name, "")

    def test_company_deletion_keeps_contact(self) -> None:
        contact = Contact.objects.create(company=self.company, full_name="Elena Ruiz")
        self.company.delete()
        contact.refresh_from_db()
        self.assertIsNone(contact.company_id)
        self.assertEqual(Contact.objects.count(), 1)
