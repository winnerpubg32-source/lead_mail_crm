"""Row-normalization tests: the data-quality rules from the brief."""

from __future__ import annotations

from django.test import SimpleTestCase

from apps.imports.records import (
    MappingError,
    build_plan,
    build_record,
    is_valid_email,
    parse_employee_count,
)

HEADERS = [
    "Business Name",
    "Contact",
    "E-mail",
    "Phone",
    "Website",
    "Address",
    "City",
    "State",
    "ZIP",
    "Employees",
]
MAPPING = {
    "Business Name": "company_name",
    "Contact": "contact_name",
    "E-mail": "email",
    "Phone": "phone",
    "Website": "website",
    "Address": "street_address",
    "City": "city",
    "State": "state",
    "ZIP": "zip_code",
    "Employees": "employee_count",
}


def record_for(values: list[str], mapping: dict[str, str | None] | None = None):
    plan = build_plan(HEADERS, mapping or MAPPING)
    return build_record(2, values, plan)


class PlanTests(SimpleTestCase):
    def test_plan_resolves_columns_and_hints(self):
        plan = build_plan(
            ["Business Name", "Mobile"], {"Business Name": "company_name", "Mobile": "phone"}
        )
        self.assertEqual(plan.fields["company_name"][1], "Business Name")
        self.assertEqual(plan.fields["phone"][2], "MOBILE")
        self.assertEqual(
            plan.column_mapping(), {"Business Name": "company_name", "Mobile": "phone"}
        )

    def test_unknown_field_is_rejected(self):
        with self.assertRaises(MappingError):
            build_plan(["Business Name"], {"Business Name": "favourite_colour"})

    def test_second_column_for_the_same_field_is_ignored(self):
        plan = build_plan(["Email", "Backup Email"], {"Email": "email", "Backup Email": "email"})
        self.assertEqual(plan.fields["email"][1], "Email")
        self.assertEqual(set(plan.fields), {"email"})

    def test_unmapped_columns_are_absent_but_listed(self):
        plan = build_plan(
            ["Notes", "Business Name"], {"Notes": None, "Business Name": "company_name"}
        )
        self.assertEqual(plan.column_mapping(), {"Notes": None, "Business Name": "company_name"})

    def test_auto_detection_is_used_when_no_mapping_is_given(self):
        plan = build_plan(["Business Name", "Corporate Email"], {})
        self.assertTrue(plan.has("company_name"))
        self.assertTrue(plan.has("email"))


class EmailTests(SimpleTestCase):
    def test_syntax_validation(self):
        for address in ("a@b.co", "first.last+tag@sub.example.com", "USER@Example.COM"):
            with self.subTest(address=address):
                self.assertTrue(is_valid_email(address) or address.isupper())
        for address in (
            "not-an-email",
            "a@b",
            "a@@b.com",
            "a b@c.com",
            "@example.com",
            "user@.com",
            "",
        ):
            with self.subTest(address=address):
                self.assertFalse(is_valid_email(address))

    def test_valid_addresses_are_normalized(self):
        record = record_for(
            ["Acme Ltd", "Jane Doe", "  JANE.DOE@Example.COM ", "", "", "", "", "", "", ""]
        )
        self.assertEqual(record.email, "jane.doe@example.com")
        self.assertEqual(record.normalized_email, "jane.doe@example.com")

    def test_invalid_address_is_dropped_not_repaired(self):
        record = record_for(
            ["Acme Ltd", "Jane Doe", "jane(at)example.com", "", "", "", "", "", "", ""]
        )
        self.assertEqual(record.email, "")
        self.assertEqual(record.normalized_email, "")
        self.assertTrue(any("invalid e-mail" in issue.message.lower() for issue in record.issues))

    def test_missing_email_is_not_an_error(self):
        record = record_for(["Acme Ltd", "Jane Doe", "", "", "", "", "", "", "", ""])
        self.assertEqual(record.email, "")
        self.assertEqual(record.issues, [])
        self.assertTrue(record.is_usable)

    def test_email_without_a_person_still_produces_a_contact(self):
        record = record_for(["Acme Ltd", "", "info@acme.com", "", "", "", "", "", "", ""])
        self.assertFalse(record.has_person)
        self.assertTrue(record.needs_contact)


class PhoneTests(SimpleTestCase):
    def test_numbers_are_normalized(self):
        record = record_for(["Acme Ltd", "Jane", "", "(614) 555-0142", "", "", "", "", "", ""])
        self.assertEqual(record.contact_phone, "6145550142")
        self.assertEqual(record.company_phone, "6145550142")
        self.assertEqual(record.phone, "6145550142")

    def test_international_prefix_is_kept(self):
        record = record_for(["Acme Ltd", "Jane", "", "+1 614 555 0142", "", "", "", "", "", ""])
        self.assertEqual(record.phone, "+16145550142")

    def test_phone_type_comes_from_the_column_name(self):
        headers = ["Business Name", "Contact", "Mobile"]
        plan = build_plan(
            headers, {"Business Name": "company_name", "Contact": "contact_name", "Mobile": "phone"}
        )
        record = build_record(2, ["Acme Ltd", "Jane", "614 555 0142"], plan)
        self.assertEqual(record.phone_type, "MOBILE")
        self.assertEqual(record.phone, "6145550142")

        # No phone column at all → unknown, not a guess.
        plain = build_plan(HEADERS, MAPPING)
        self.assertEqual(
            build_record(2, ["Acme Ltd", "Jane", "", "", "", "", "", "", "", ""], plain).phone_type,
            "UNKNOWN",
        )

    def test_a_direct_line_outranks_the_switchboard(self):
        headers = ["Business Name", "Contact", "Phone", "Direct Dial"]
        plan = build_plan(
            headers,
            {
                "Business Name": "company_name",
                "Contact": "contact_name",
                "Phone": "company_phone",
                "Direct Dial": "contact_phone",
            },
        )
        record = build_record(2, ["Acme Ltd", "Jane", "614-555-0100", "614-555-0188"], plan)
        self.assertEqual(record.company_phone, "6145550100")
        self.assertEqual(record.contact_phone, "6145550188")
        self.assertEqual(record.phone, "6145550188")


class EmployeeCountTests(SimpleTestCase):
    def test_parses_messy_shapes(self):
        cases = {
            "1,200": 1200,
            "50-100": 50,
            "250+": 250,
            "  About 42 ": 42,
            "": None,
            "n/a": None,
            "unknown": None,
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(parse_employee_count(value), expected)

    def test_record_keeps_the_parsed_number(self):
        record = record_for(["Acme Ltd", "", "", "", "", "", "", "", "", "40-60"])
        self.assertEqual(record.employee_count, 40)


class NormalizationTests(SimpleTestCase):
    def test_company_name_address_and_city_are_cleaned(self):
        record = record_for(
            [
                "  Northwind   Logistics, Inc. ",
                "",
                "",
                "",
                "HTTPS://WWW.NorthwindLogistics.com/about?utm=1",
                " 1200   Meridian Plaza ",
                " columbus ",
                " oh ",
                " 43215 ",
                "",
            ]
        )
        self.assertEqual(record.company_name, "Northwind Logistics, Inc.")
        self.assertEqual(record.normalized_name, "northwind logistics")
        self.assertEqual(record.domain, "northwindlogistics.com")
        self.assertEqual(record.street_address, "1200 Meridian Plaza")
        self.assertEqual(record.city, "columbus")
        self.assertEqual(record.state, "oh")

    def test_person_names_are_split_and_titles_dropped(self):
        record = record_for(["Acme Ltd", "Dr. Elena Ruiz", "", "", "", "", "", "", "", ""])
        self.assertEqual((record.first_name, record.last_name), ("Elena", "Ruiz"))
        self.assertEqual(record.contact_name, "Dr. Elena Ruiz")

    def test_separate_first_and_last_name_win(self):
        values = ["Acme Ltd", "", "", "", "", "", "", "", "", ""]
        plan = build_plan(
            [*HEADERS, "First Name", "Last Name"],
            {**MAPPING, "First Name": "first_name", "Last Name": "last_name"},
        )
        record = build_record(2, [*values, "Marcus", "Whitfield"], plan)
        self.assertEqual(record.contact_name, "Marcus Whitfield")

    def test_country_defaults_to_the_united_states(self):
        record = record_for(["Acme Ltd", "", "", "", "", "", "", "", "", ""])
        self.assertEqual(record.country, "United States")

    def test_name_of_only_legal_suffixes_does_not_collapse(self):
        record = record_for(["Inc.", "", "", "", "", "", "", "", "", ""])
        self.assertNotEqual(record.normalized_name, "")
        self.assertEqual(record.company_key, "name:inc.")


class RowShapeTests(SimpleTestCase):
    def test_row_without_a_business_name_is_not_usable(self):
        record = record_for(["", "Jane Doe", "jane@acme.com", "", "", "", "", "", "", ""])
        self.assertFalse(record.is_usable)

    def test_short_row_is_flagged_as_misaligned(self):
        record = build_record(7, ["Acme Ltd", "Jane"], build_plan(HEADERS, MAPPING))
        self.assertTrue(any("header has" in issue.message for issue in record.issues))
        self.assertEqual(record.issues[0].row, 7)

    def test_keys_used_for_deduplication(self):
        record = record_for(
            ["Acme Ltd", "Jane Doe", "jane@acme.com", "", "acme.com", "", "", "", "", ""]
        )
        self.assertEqual(record.company_key, "domain:acme.com")
        self.assertEqual(record.contact_key, "email:jane@acme.com")

        without_email = record_for(["Acme Ltd", "Jane Doe", "", "", "acme.com", "", "", "", "", ""])
        self.assertEqual(without_email.contact_key, "name:jane doe")
