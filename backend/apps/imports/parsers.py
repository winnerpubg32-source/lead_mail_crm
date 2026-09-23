"""
Streaming readers for the uploaded CSV / XLSX files.

Both readers are generators over *physical* rows, so a 500 000-row export is
processed with a constant memory footprint:

* CSV — :mod:`csv` over a text file handle, with encoding fallback
  (UTF-8 → CP1252 → Latin-1) and delimiter sniffing (``,`` ``;`` ``\\t`` ``|``).
* XLSX — ``openpyxl`` in ``read_only=True`` mode, which streams the shared
  strings and worksheet XML instead of materialising the sheet.

Nothing here touches the database or Django: the parsers only turn bytes into
``Row(number, values)`` tuples, which makes them easy to unit test.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "CSV_EXTENSIONS",
    "XLSX_EXTENSIONS",
    "DetectedFile",
    "Row",
    "detect_delimiter",
    "detect_encoding",
    "detect_file_type",
    "header_row",
    "iter_rows",
    "list_sheets",
    "normalize_headers",
    "read_table",
]

CSV_EXTENSIONS = frozenset({".csv", ".txt", ".tsv"})
XLSX_EXTENSIONS = frozenset({".xlsx", ".xlsm"})

#: Fallbacks are tried in this order; latin-1 can decode any byte sequence.
ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")
#: Delimiters the sniffer is allowed to choose from.
DELIMITERS = ",;\t|"
SAMPLE_BYTES = 64 * 1024


class UnsupportedFileType(ValueError):
    """Raised when an upload is neither a CSV nor an XLSX file."""


@dataclass(frozen=True)
class Row:
    """One physical data row: 1-based number in the file plus its cell values."""

    number: int
    values: list[str]


@dataclass(frozen=True)
class DetectedFile:
    """What the parser worked out about an upload before reading the rows."""

    file_type: str  # "csv" | "xlsx"
    encoding: str = ""
    delimiter: str = ""
    sheets: tuple[str, ...] = ()

    @property
    def sheet_count(self) -> int:
        return len(self.sheets)


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------
def detect_file_type(path: str | Path, filename: str = "") -> str:
    """
    Decide between CSV and XLSX from the extension, then from the file magic.

    XLSX files are ZIP archives, so a renamed spreadsheet is still recognised
    instead of being read as binary garbage.
    """
    name = (filename or Path(path).name).lower()
    suffix = Path(name).suffix

    if suffix in XLSX_EXTENSIONS:
        return "xlsx"

    # Content beats the extension: spreadsheets are ZIP containers, so a renamed
    # .csv/.txt file is still read as XLSX instead of producing binary garbage.
    if zipfile.is_zipfile(path):
        return "xlsx"

    if suffix in CSV_EXTENSIONS:
        return "csv"

    raise UnsupportedFileType(f"Unsupported file type: {name or path}")


def detect_encoding(path: str | Path) -> str:
    """First encoding from :data:`ENCODINGS` that decodes the head of the file."""
    with open(path, "rb") as handle:
        sample = handle.read(SAMPLE_BYTES)
    for encoding in ENCODINGS:
        try:
            sample.decode(encoding)
        except UnicodeDecodeError:
            continue
        return encoding
    return "latin-1"


def _sniff_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample, delimiters=DELIMITERS).delimiter
    except csv.Error:
        return "\t" if sample.count("\t") > sample.count(",") else ","


def detect_delimiter(path: str | Path, encoding: str | None = None) -> str:
    """Delimiter used by a CSV file (``,`` ``;`` tab or ``|``)."""
    charset = encoding or detect_encoding(path)
    with open(path, encoding=charset, errors="replace", newline="") as handle:
        return _sniff_delimiter(handle.read(SAMPLE_BYTES))


def list_sheets(path: str | Path, file_type: str) -> tuple[str, ...]:
    """Worksheet names for XLSX files; CSV files have no sheets."""
    if file_type != "xlsx":
        return ()
    from openpyxl import load_workbook

    workbook = load_workbook(filename=str(path), read_only=True, data_only=True)
    try:
        return tuple(workbook.sheetnames)
    finally:
        workbook.close()


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------
def _iter_csv(path: str | Path, encoding: str, delimiter: str) -> Iterator[Row]:
    with open(path, encoding=encoding, errors="replace", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        for values in reader:
            if not any(str(cell).strip() for cell in values):
                continue  # blank separator line
            yield Row(number=reader.line_num, values=[str(cell) for cell in values])


# ---------------------------------------------------------------------------
# XLSX
# ---------------------------------------------------------------------------
def _cell_to_text(value: object) -> str:
    """Render a spreadsheet cell as the string the normalizers expect."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, dt.datetime):
        return (
            value.date().isoformat() if value.time() == dt.time(0, 0) else value.isoformat(sep=" ")
        )
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else repr(value).rstrip("0").rstrip(".")
    return str(value)


def _iter_xlsx(path: str | Path, sheet: str | None) -> Iterator[Row]:
    from openpyxl import load_workbook

    workbook = load_workbook(filename=str(path), read_only=True, data_only=True)
    try:
        worksheet = workbook[sheet] if sheet and sheet in workbook.sheetnames else workbook.active
        for index, values in enumerate(worksheet.iter_rows(values_only=True), start=1):
            cells = [_cell_to_text(value) for value in values]
            if not any(cell.strip() for cell in cells):
                continue
            yield Row(number=index, values=cells)
    finally:
        workbook.close()


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------
def iter_rows(
    path: str | Path,
    file_type: str,
    *,
    sheet: str | None = None,
    encoding: str | None = None,
    delimiter: str | None = None,
) -> Iterator[Row]:
    """Yield every non-empty physical row of the file, in order."""
    if file_type == "xlsx":
        return _iter_xlsx(path, sheet)

    chosen_encoding = encoding or detect_encoding(path)
    chosen_delimiter = delimiter or detect_delimiter(path, chosen_encoding)
    return _iter_csv(path, chosen_encoding, chosen_delimiter)


def normalize_headers(values: list[str]) -> list[str]:
    """
    Clean up the header row: trim, drop formatting noise, fill in blanks and
    make duplicates unique (``Email``, ``Email (2)``).

    The original spelling is preserved — it is what the user sees in the
    mapping table and in the preview.
    """
    headers: list[str] = []
    seen: dict[str, int] = {}

    for index, raw in enumerate(values, start=1):
        label = " ".join(str(raw).replace("\ufeff", " ").split()).strip()
        if not label:
            label = f"Column {index}"

        count = seen.get(label.lower(), 0) + 1
        seen[label.lower()] = count
        headers.append(label if count == 1 else f"{label} ({count})")

    return headers


def header_row(
    path: str | Path, file_type: str, *, sheet: str | None = None, **kwargs
) -> list[str]:
    """First non-empty row of the file, normalized into unique column names."""
    for row in iter_rows(path, file_type, sheet=sheet, **kwargs):
        return normalize_headers(row.values)
    return []


def read_table(
    path: str | Path,
    file_type: str,
    *,
    sheet: str | None = None,
    **kwargs,
) -> tuple[list[str], Iterator[Row]]:
    """
    Return ``(headers, data_rows)`` where ``data_rows`` is a lazy generator that
    has already skipped the header line.
    """
    rows = iter_rows(path, file_type, sheet=sheet, **kwargs)
    headers: list[str] = []
    for row in rows:
        headers = normalize_headers(row.values)
        break

    return headers, iter(rows)


def sample_bytes(path: str | Path, size: int = SAMPLE_BYTES) -> bytes:
    """Small helper used by tests and the preview to show the raw head."""
    with open(path, "rb") as handle:
        return io.BytesIO(handle.read(size)).getvalue()
