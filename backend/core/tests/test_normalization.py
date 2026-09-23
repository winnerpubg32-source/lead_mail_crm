"""Unit tests for the shared normalisation helpers."""

from __future__ import annotations

from django.test import SimpleTestCase

from core.normalization import (
    build_full_name,
    company_name_key,
    normalize_company_name,
    normalize_domain,
    normalize_email,
    normalize_phone,
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
