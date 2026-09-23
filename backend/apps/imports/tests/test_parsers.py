"""Parser tests: CSV dialects, encodings, XLSX sheets and cell types."""

from __future__ import annotations

import datetime as dt
import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from apps.imports.parsers import (
    UnsupportedFileType,
    detect_delimiter,
    detect_encoding,
    detect_file_type,
    header_row,
    iter_rows,
    list_sheets,
    normalize_headers,
    read_table,
)
from apps.imports.tests.factories import write_csv, write_xlsx


class TempFilesMixin:
    def setUp(self):
        super().setUp()
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()
        super().tearDown()


class FileTypeTests(TempFilesMixin, SimpleTestCase):
    def test_extensions(self):
        self.assertEqual(detect_file_type("a/b/leads.csv"), "csv")
        self.assertEqual(detect_file_type("leads.XLSX"), "xlsx")
        self.assertEqual(detect_file_type("leads.tsv"), "csv")

    def test_zip_magic_wins_over_a_misleading_extension(self):
        path = write_xlsx(self.tmp / "data.txt")
        self.assertEqual(detect_file_type(path, "data.txt"), "xlsx")

    def test_unsupported_files_are_rejected(self):
        path = self.tmp / "notes.pdf"
        path.write_bytes(b"%PDF-1.4 not a spreadsheet")
        with self.assertRaises(UnsupportedFileType):
            detect_file_type(path, "notes.pdf")


class CsvTests(TempFilesMixin, SimpleTestCase):
    def test_reads_rows_and_skips_blank_lines(self):
        path = write_csv(
            self.tmp / "leads.csv",
            [["Name", "Email"], ["Acme", "a@acme.com"], [], ["Beta", "b@beta.com"]],
        )
        headers, rows = read_table(path, "csv")
        self.assertEqual(headers, ["Name", "Email"])
        self.assertEqual(
            [row.values for row in rows], [["Acme", "a@acme.com"], ["Beta", "b@beta.com"]]
        )

    def test_row_numbers_point_at_the_file_lines(self):
        path = write_csv(self.tmp / "leads.csv", [["Name"], ["Acme"], ["Beta"]])
        _, rows = read_table(path, "csv")
        # Line 1 is the header, so the data starts at line 2.
        self.assertEqual([row.number for row in rows], [2, 3])

    def test_semicolon_and_tab_delimiters_are_detected(self):
        for delimiter in (";", "\t", "|"):
            with self.subTest(delimiter=delimiter):
                path = write_csv(
                    self.tmp / "leads.csv",
                    [["Name", "City"], ["Acme", "Austin"]],
                    delimiter=delimiter,
                )
                self.assertEqual(detect_delimiter(path, "utf-8"), delimiter)
                headers, rows = read_table(path, "csv")
                self.assertEqual(headers, ["Name", "City"])
                self.assertEqual([row.values for row in rows], [["Acme", "Austin"]])

    def test_windows_1252_files_are_decoded(self):
        path = self.tmp / "latin.csv"
        path.write_bytes("Name,City\nCafé Sàrl,Montréal\n".encode("cp1252"))
        self.assertEqual(detect_encoding(path), "utf-8-sig".replace("utf-8-sig", "cp1252"))
        _, rows = read_table(path, "csv")
        self.assertEqual([row.values for row in rows], [["Café Sàrl", "Montréal"]])

    def test_utf8_bom_is_stripped(self):
        path = self.tmp / "bom.csv"
        path.write_bytes("\ufeffName,City\nAcme,Austin\n".encode())
        self.assertEqual(header_row(path, "csv"), ["Name", "City"])

    def test_quoted_fields_with_delimiters_and_newlines(self):
        path = self.tmp / "quoted.csv"
        path.write_bytes(b'Name,Notes\n"Acme, Inc.","Line one\nLine two"\n')
        headers, rows = read_table(path, "csv")
        self.assertEqual(len(headers), 2)
        self.assertEqual([row.values for row in rows], [["Acme, Inc.", "Line one\nLine two"]])


class HeaderTests(SimpleTestCase):
    def test_blank_headers_get_positional_names(self):
        self.assertEqual(normalize_headers(["Name", "", "  "]), ["Name", "Column 2", "Column 3"])

    def test_duplicate_headers_are_made_unique(self):
        self.assertEqual(
            normalize_headers(["Email", "email", "Email"]), ["Email", "email (2)", "Email (3)"]
        )

    def test_whitespace_and_bom_are_trimmed(self):
        self.assertEqual(normalize_headers(["\ufeff Business  Name "]), ["Business Name"])


class XlsxTests(TempFilesMixin, SimpleTestCase):
    def test_sheets_are_listed_and_selectable(self):
        path = write_xlsx(
            self.tmp / "book.xlsx",
            {"Leads": [["Company"], ["Acme"]], "Lookups": [["Industry"], ["Retail"]]},
        )
        self.assertEqual(list_sheets(path, "xlsx"), ("Leads", "Lookups"))
        self.assertEqual(header_row(path, "xlsx", sheet="Lookups"), ["Industry"])
        self.assertEqual(
            [row.values for row in iter_rows(path, "xlsx", sheet="Lookups")],
            [["Industry"], ["Retail"]],
        )

    def test_cell_types_are_converted(self):
        path = write_xlsx(
            self.tmp / "book.xlsx",
            {
                "Leads": [
                    ["Company", "Headcount", "Joined", "Rate", "Active"],
                    ["Acme", 75, dt.date(2024, 5, 1), 12.5, True],
                ]
            },
        )
        rows = iter(iter_rows(path, "xlsx"))
        header, data = next(rows), next(rows)
        self.assertEqual(header.values[0], "Company")
        self.assertEqual(data.values, ["Acme", "75", "2024-05-01", "12.5", "TRUE"])

    def test_empty_rows_are_skipped(self):
        path = write_xlsx(
            self.tmp / "book.xlsx", {"Leads": [["Company"], ["Acme"], [None, None], ["Beta"]]}
        )
        _, rows = read_table(path, "xlsx")
        # openpyxl pads rows to the sheet width, so both rows carry the same
        # number of cells as the header — that keeps alignment checks honest.
        self.assertEqual([row.values for row in rows], [["Acme", ""], ["Beta", ""]])

    def test_csv_files_have_no_sheets(self):
        path = write_csv(self.tmp / "leads.csv", [["Company"], ["Acme"]])
        self.assertEqual(list_sheets(path, "csv"), ())
