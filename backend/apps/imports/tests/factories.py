"""Helpers that build real CSV / XLSX uploads for the import tests."""

from __future__ import annotations

import datetime as dt
import io
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile


def csv_bytes(rows: list[list[str]], delimiter: str = ",", encoding: str = "utf-8") -> bytes:
    """Serialise rows to CSV bytes, quoting fields that contain the delimiter."""
    lines: list[str] = []
    for row in rows:
        cells = []
        for value in row:
            text = str(value)
            if delimiter in text or '"' in text or "\n" in text:
                text = '"' + text.replace('"', '""') + '"'
            cells.append(text)
        lines.append(delimiter.join(cells))
    return ("\n".join(lines) + "\n").encode(encoding)


def csv_upload(rows: list[list[str]], name: str = "businesses.csv", **kwargs) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, csv_bytes(rows, **kwargs), content_type="text/csv")


def write_csv(path: Path, rows: list[list[str]], **kwargs) -> Path:
    path.write_bytes(csv_bytes(rows, **kwargs))
    return path


def _build_workbook(sheets: dict[str, list[list[object]]]):
    """A real openpyxl workbook with one named sheet per entry."""
    from openpyxl import Workbook

    workbook = Workbook()
    default = workbook.active
    for index, (title, content) in enumerate(sheets.items()):
        sheet = default if index == 0 else workbook.create_sheet()
        sheet.title = title
        for row in content:
            sheet.append(row)
    return workbook


def write_xlsx(path: Path, sheets: dict[str, list[list[object]]] | None = None) -> Path:
    """Write a real .xlsx workbook, optionally with extra sheets."""
    _build_workbook(sheets or {"Leads": []}).save(path)
    return path


def xlsx_upload(
    sheets: dict[str, list[list[object]]] | None = None,
    name: str = "businesses.xlsx",
) -> SimpleUploadedFile:
    """An ``.xlsx`` upload ready to POST to the import endpoint."""
    buffer = io.BytesIO()
    _build_workbook(sheets or {"Leads": []}).save(buffer)
    return SimpleUploadedFile(
        name,
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


#: A small, deliberately messy dataset used by several suites: alias column
#: names, a duplicate row, an invalid address and a row without a company name.
MESSY_HEADERS = [
    "Business_Name",
    "Contact Person",
    "Job Title",
    "Corporate Email",
    "Mobile",
    "Company Website",
    "Industry",
    "Address",
    "City",
    "State",
    "ZIP",
    "Employees",
]

MESSY_ROWS = [
    MESSY_HEADERS,
    [
        "Northwind Logistics, Inc.",
        "Marcus Whitfield",
        "VP Operations",
        "m.whitfield@northwindlogistics.com",
        "(614) 555-0142",
        "https://www.northwindlogistics.com",
        "Transportation & Logistics",
        "1200 Meridian Plaza",
        "Columbus",
        "OH",
        "43215",
        "850",
    ],
    [
        "Brightline Dental Group",
        "Elena Ruiz",
        "Managing Partner",
        "elena.ruiz@brightlinedental.com",
        "813-555-0188",
        "brightlinedental.com",
        "Healthcare",
        "88 Bayshore Blvd",
        "Tampa",
        "FL",
        "33606",
        "40-60",
    ],
    [
        "Bluewater Marine Supply",
        "Sofia Marchetti",
        "Purchasing Manager",
        "not-an-email",
        "305-555-0166",
        "bluewatermarine.com",
        "Retail",
        "900 Biscayne Blvd",
        "Miami",
        "FL",
        "33132",
        "65",
    ],
    [
        "Northwind Logistics, Inc.",
        "Marcus Whitfield",
        "VP Operations",
        "m.whitfield@northwindlogistics.com",
        "(614) 555-0142",
        "https://www.northwindlogistics.com",
        "Transportation & Logistics",
        "1200 Meridian Plaza",
        "Columbus",
        "OH",
        "43215",
        "850",
    ],
    [
        "",
        "Unknown Person",
        "Analyst",
        "orphan@nowhere.com",
        "555-000-0000",
        "",
        "Unknown",
        "",
        "",
        "",
        "",
        "",
    ],
]

#: Values the tests expect for the XLSX variant (typed cells, not strings).
XLSX_ROWS: list[list[object]] = [
    [
        "Company",
        "Owner",
        "E-mail Address",
        "Telephone",
        "URL",
        "Town",
        "State",
        "Headcount",
        "Joined",
    ],
    [
        "Cascade Brewing Co.",
        "Tomas Lindqvist",
        "tomas@cascadebrewing.com",
        "503-555-0121",
        "cascadebrewing.com",
        "Portland",
        "OR",
        75,
        dt.date(2024, 5, 1),
    ],
    [
        "Summit Peak Wealth",
        "Barbara Osei",
        "b.osei@summitpeakwealth.com",
        "(303) 555-0155",
        "summitpeakwealth.com",
        "Denver",
        "CO",
        45,
        dt.date(2023, 11, 14),
    ],
]
