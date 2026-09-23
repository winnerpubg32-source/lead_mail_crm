"""
Column-detection tests.

The first block is the alias list from the product brief — every one of those
headers must map to the documented system field. The rest pins the behaviour
that keeps the mapper trustworthy: typos are tolerated by the fuzzy layer,
generic columns stay unmapped, and two columns never feed the same field.
"""

from __future__ import annotations

from django.test import SimpleTestCase

from apps.imports.mapping import (
    SYSTEM_FIELDS,
    detect_field,
    detect_mapping,
    normalize_header,
    phone_type_for_header,
    system_fields_payload,
)

BRIEF_EXAMPLES: dict[str, list[str]] = {
    "company_name": ["Business Name", "Company Name", "Company", "Organization", "Business"],
    "email": ["Email", "Email Address", "E-mail", "Corporate Email", "Primary Email"],
    "contact_name": ["Contact", "Contact Person", "Owner", "Owner Name", "Contact Name"],
    "first_name": ["First Name", "Firstname"],
    "website": ["Website", "Website URL", "URL", "Web"],
    "phone": ["Phone", "Phone Number", "Telephone", "Mobile"],
    "street_address": ["Address", "Street Address", "Street"],
    "zip_code": ["ZIP", "Zip Code", "Postal Code"],
    "state": ["State"],
    "city": ["City"],
}

#: Headers that must stay unmapped — mapping them would corrupt the database.
UNMAPPABLE = [
    "ID",
    "Record No",
    "Company ID",
    "Type",
    "Revenue",
    "Notes",
    "favorite color",
    "random text",
    "Unnamed: 3",
    "",
]


class NormalizeHeaderTests(SimpleTestCase):
    def test_collapses_punctuation_case_and_accents(self):
        self.assertEqual(normalize_header("  Business__Name "), "business name")
        self.assertEqual(normalize_header("E-mail Address"), "e mail address")
        self.assertEqual(normalize_header("Organización"), "organizacion")
        self.assertEqual(normalize_header("M&A Contact"), "m and a contact")
        self.assertEqual(normalize_header(None), "")


class BriefExampleTests(SimpleTestCase):
    def test_every_brief_example_maps_to_its_field(self):
        for expected, headers in BRIEF_EXAMPLES.items():
            for header in headers:
                with self.subTest(header=header):
                    self.assertEqual(detect_field(header).field, expected)

    def test_detection_reports_how_it_matched(self):
        exact = detect_field("Business Name")
        self.assertEqual(exact.method, "exact")
        self.assertEqual(exact.confidence, 1.0)

        alias = detect_field("Corporate Email")
        self.assertEqual(alias.method, "alias")
        self.assertEqual(alias.label, "E-mail")
        self.assertEqual(alias.matched_on, "corporate email")

    def test_mobile_columns_carry_a_phone_type_hint(self):
        self.assertEqual(detect_field("Mobile").hint, "MOBILE")
        self.assertEqual(detect_field("Cell Phone").hint, "MOBILE")
        self.assertEqual(detect_field("WhatsApp Number").hint, "MOBILE")
        self.assertEqual(detect_field("Landline").hint, "LANDLINE")
        self.assertEqual(detect_field("Office Phone").hint, "OFFICE")
        self.assertEqual(detect_field("Phone").hint, "")

    def test_phone_type_for_header(self):
        self.assertEqual(phone_type_for_header("cell phone"), "MOBILE")
        self.assertEqual(phone_type_for_header("switchboard"), "OFFICE")
        self.assertEqual(phone_type_for_header("extension"), "")


class FuzzyAndSafetyTests(SimpleTestCase):
    def test_typos_are_recovered(self):
        """A typo must still land on the right field, via fuzzy or alias."""
        for header in ("Busines Name", "Compnay Name", "Business Nmae", "E Mail Adress"):
            with self.subTest(header=header):
                match = detect_field(header)
                self.assertIn(match.field, {"company_name", "email"})
                self.assertIn(match.method, {"alias", "fuzzy"})
                self.assertGreaterEqual(match.confidence, 0.84)

    def test_fuzzy_layer_is_used_when_no_alias_matches(self):
        match = detect_field("Busines Name")
        self.assertEqual(match.field, "company_name")
        self.assertEqual(match.method, "fuzzy")

    def test_unseen_aliases_map_through_tokens_or_fuzzy(self):
        expected = {
            "Business_Name": "company_name",
            "Org Name": "company_name",
            "Work Email": "email",
            "Contact Full Name": "contact_name",
            "Primary Contact": "contact_name",
            "Decision Maker": "contact_name",
            "Telephone Number": "phone",
            "Post Code": "zip_code",
            "Province": "state",
            "Town": "city",
            "Headcount": "employee_count",
            "Contact Title": "job_title",
            "Given Name": "first_name",
            "Surname": "last_name",
            "Company Website": "website",
        }
        for header, field in expected.items():
            with self.subTest(header=header):
                self.assertEqual(detect_field(header).field, field)

    def test_generic_columns_stay_unmapped(self):
        for header in UNMAPPABLE:
            with self.subTest(header=header):
                self.assertIsNone(detect_field(header).field)

    def test_identifier_suffix_is_not_a_name(self):
        # "Company ID" is a key; "Zip Code" legitimately keeps its "code".
        self.assertIsNone(detect_field("Company ID").field)
        self.assertEqual(detect_field("Zip Code").field, "zip_code")
        self.assertEqual(detect_field("Phone No.").field, "phone")

    def test_unmapped_columns_still_offer_candidates(self):
        match = detect_field("favorite color")
        self.assertIsNone(match.field)
        self.assertTrue(match.candidates)
        self.assertTrue(all(isinstance(key, str) for key, _score in match.candidates))


class DetectMappingTests(SimpleTestCase):
    def test_one_field_is_never_fed_by_two_columns(self):
        matches = detect_mapping(
            ["Company Name", "Business", "E-mail", "Email Address", "Phone", "Mobile"]
        )
        mapping = {match.column: match.field for match in matches}

        self.assertEqual(mapping["Company Name"], "company_name")
        self.assertEqual(mapping["E-mail"], "email")
        self.assertEqual(mapping["Phone"], "phone")
        # The losers of each collision are reset so the user decides in the UI.
        self.assertIsNone(mapping["Business"])
        self.assertIsNone(mapping["Email Address"])
        self.assertIsNone(mapping["Mobile"])

    def test_higher_confidence_wins_the_collision(self):
        matches = detect_mapping(["Email", "Primary Email"])
        mapping = {match.column: match.field for match in matches}
        self.assertEqual(mapping["Email"], "email")
        self.assertIsNone(mapping["Primary Email"])

    def test_left_most_wins_when_confidence_is_equal(self):
        matches = detect_mapping(["Company Name", "Business Name"])
        mapping = {match.column: match.field for match in matches}
        self.assertEqual(mapping["Company Name"], "company_name")
        self.assertIsNone(mapping["Business Name"])

    def test_catalog_payload_matches_the_field_table(self):
        payload = system_fields_payload()
        self.assertEqual(len(payload), len(SYSTEM_FIELDS))
        self.assertEqual(payload[0]["key"], "company_name")
        self.assertTrue(payload[0]["required"])
        self.assertIn("business name", payload[0]["aliases"])
