"""Unit tests for the shared normalisation helpers."""

from __future__ import annotations

from django.test import SimpleTestCase

from core.normalization import (
    address_key,
    build_full_name,
    company_name_key,
    normalize_address,
    normalize_company_name,
    normalize_contact_name,
    normalize_domain,
    normalize_email,
    normalize_name_case,
    normalize_phone,
    normalize_state,
    normalize_whitespace,
    split_full_name,
)


class WhitespaceTests(SimpleTestCase):
    def test_collapses_and_trims(self) -> None:
        self.assertEqual(normalize_whitespace("  Acme   Corp \n"), "Acme Corp")

    def test_handles_none_and_empty(self) -> None:
        self.assertEqual(normalize_whitespace(None), "")
        self.assertEqual(normalize_whitespace("   "), "")


class CompanyNameTests(SimpleTestCase):
    def test_removes_legal_suffixes_and_punctuation(self) -> None:
        self.assertEqual(normalize_company_name("Northwind Logistics, Inc."), "northwind logistics")
        self.assertEqual(normalize_company_name("ACME LLC"), "acme")
        self.assertEqual(
            normalize_company_name("Vertex Precision Mfg. Co."), "vertex precision mfg"
        )

    def test_folds_case_and_accents(self) -> None:
        self.assertEqual(normalize_company_name("Café Réseau SARL"), "cafe reseau")

    def test_expands_ampersand(self) -> None:
        self.assertEqual(normalize_company_name("Bright & Co"), "bright and")

    def test_matching_key_ignores_spacing(self) -> None:
        self.assertEqual(
            company_name_key("Brightline  Dental"), company_name_key("brightlinedental")
        )


class WebsiteTests(SimpleTestCase):
    def test_strips_scheme_path_and_www(self) -> None:
        self.assertEqual(
            normalize_domain("https://www.NorthwindLogistics.com/about?utm_source=x"),
            "northwindlogistics.com",
        )

    def test_accepts_bare_domain_with_trailing_slash(self) -> None:
        self.assertEqual(normalize_domain("NorthwindLogistics.COM/"), "northwindlogistics.com")

    def test_accepts_email_shaped_input(self) -> None:
        self.assertEqual(normalize_domain("ops@Acme.co.uk"), "acme.co.uk")

    def test_removes_port(self) -> None:
        self.assertEqual(normalize_domain("acme.com:8080"), "acme.com")

    def test_blank_input(self) -> None:
        self.assertEqual(normalize_domain("   "), "")


class EmailTests(SimpleTestCase):
    def test_lowercases_and_trims(self) -> None:
        self.assertEqual(
            normalize_email("  Marcus.Whitfield@Northwind.com "), "marcus.whitfield@northwind.com"
        )

    def test_rejects_malformed_addresses(self) -> None:
        self.assertEqual(normalize_email("not-an-email"), "")
        self.assertEqual(normalize_email("user@localhost"), "")
        self.assertEqual(normalize_email(""), "")

    def test_strips_illegal_characters(self) -> None:
        self.assertEqual(normalize_email("bad<script>@acme.com"), "badscript@acme.com")


class PhoneTests(SimpleTestCase):
    def test_digits_only_for_domestic_numbers(self) -> None:
        self.assertEqual(normalize_phone("(614) 555-0142"), "6145550142")

    def test_keeps_international_prefix(self) -> None:
        self.assertEqual(normalize_phone("+1 614 555 0142"), "+16145550142")

    def test_empty_input(self) -> None:
        self.assertEqual(normalize_phone(""), "")
        self.assertEqual(normalize_phone("n/a"), "")


class NameTests(SimpleTestCase):
    def test_build_full_name(self) -> None:
        self.assertEqual(build_full_name("Elena", "Ruiz"), "Elena Ruiz")
        self.assertEqual(build_full_name("Elena", ""), "Elena")
        self.assertEqual(build_full_name("", ""), "")

    def test_split_full_name_drops_titles(self) -> None:
        self.assertEqual(split_full_name("Dr. Elena Ruiz"), ("Elena", "Ruiz"))

    def test_split_full_name_handles_single_token(self) -> None:
        self.assertEqual(split_full_name("Prince"), ("Prince", ""))

    def test_split_full_name_keeps_multi_part_first_names(self) -> None:
        self.assertEqual(split_full_name("Ana Maria Delgado"), ("Ana Maria", "Delgado"))

    def test_split_full_name_handles_blank(self) -> None:
        self.assertEqual(split_full_name(None), ("", ""))


class ContactNameTests(SimpleTestCase):
    def test_lowercases_and_strips_punctuation(self) -> None:
        self.assertEqual(
            normalize_contact_name(" Dr.  Maria", "O'Brien"), "maria o brien"
        )

    def test_folds_accents(self) -> None:
        self.assertEqual(normalize_contact_name("José", "García"), "jose garcia")

    def test_blank_input(self) -> None:
        self.assertEqual(normalize_contact_name(None, None), "")
        self.assertEqual(normalize_contact_name("", ""), "")


class AddressTests(SimpleTestCase):
    def test_strips_punctuation_and_abbrev(self) -> None:
        self.assertEqual(
            normalize_address("123 Main Street", "Columbus", "OH", "43215"),
            "123 main st columbus oh 43215",
        )

    def test_shortens_suffixes(self) -> None:
        self.assertEqual(
            normalize_address("456 Elm Avenue, Suite 200", "Austin", "Texas"),
            "456 elm ave ste 200 austin tx",
        )

    def test_same_address_regardless_of_format(self) -> None:
        a = normalize_address("123 Main St.", "Columbus", "OH")
        b = normalize_address("123 Main Street", "columbus", "ohio")
        self.assertEqual(a, b)

    def test_address_key_collapses_whitespace(self) -> None:
        a = address_key("123 Main St", "Columbus", "OH")
        b = address_key("  123  Main   Street  ", "COLUMBUS", "Ohio")
        self.assertEqual(a, b)

    def test_blank_input(self) -> None:
        self.assertEqual(normalize_address(), "")
        self.assertEqual(address_key(None, None, None), "")


class StateTests(SimpleTestCase):
    def test_expands_full_names(self) -> None:
        self.assertEqual(normalize_state("ohio"), "OH")
        self.assertEqual(normalize_state("California"), "CA")
        self.assertEqual(normalize_state("  new YORK  "), "NY")

    def test_passes_through_short_codes(self) -> None:
        self.assertEqual(normalize_state("OH"), "OH")
        self.assertEqual(normalize_state("ca"), "CA")

    def test_unknown(self) -> None:
        self.assertEqual(normalize_state("Ontario"), "Ontario")


class NameCaseTests(SimpleTestCase):
    def test_title_cases(self) -> None:
        self.assertEqual(normalize_name_case("jane smith"), "Jane Smith")

    def test_blank(self) -> None:
        self.assertEqual(normalize_name_case(None), "")
        self.assertEqual(normalize_name_case(""), "")
