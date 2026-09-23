"""
Preview analysis for an uploaded file.

The preview the user confirms is produced by a **single streaming pass** over the
file: rows are normalized exactly like the importer will normalize them
(:mod:`apps.imports.records`), so the numbers cannot disagree with the run.

What is computed:

* total rows, rows with / without e-mail, rows with an invalid e-mail address;
* potential duplicates — rows whose e-mail or website domain already exists in
  the lead database, or that repeat earlier in the same file;
* the first :data:`PREVIEW_ROWS` rows, verbatim, for the table;
* per-column detection details (system field, confidence, method).

No AI, no sampling tricks: one pass, constant memory.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dc_field
from pathlib import Path

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.imports.mapping import detect_mapping
from apps.imports.parsers import (
    detect_delimiter,
    detect_encoding,
    list_sheets,
    read_table,
)
from apps.imports.records import MappingError, build_plan, build_record

__all__ = ["PREVIEW_ROWS", "AnalysisResult", "analyze_file"]

#: How many rows the preview shows (the brief asks for the first 50).
PREVIEW_ROWS = 50
#: Duplicate detection keeps sets of e-mails/domains; they are capped so a
#: multi-million-row file cannot exhaust memory.
MAX_TRACKED_KEYS = 200_000
#: How many values are looked up in the database per query.
LOOKUP_BATCH = 1_000


@dataclass
class AnalysisResult:
    """Everything the preview screen needs, cached on the job."""

    total_rows: int = 0
    rows_with_email: int = 0
    rows_without_email: int = 0
    invalid_emails: int = 0
    potential_duplicates: int = 0
    sample_rows: list[dict] = dc_field(default_factory=list)
    columns: list[dict] = dc_field(default_factory=list)
    mapping: dict[str, str | None] = dc_field(default_factory=dict)
    issues: list[dict] = dc_field(default_factory=list)

    @property
    def rows_with_company(self) -> int:
        return self.total_rows

    def as_dict(self) -> dict:
        return {
            "total_rows": self.total_rows,
            "rows_with_email": self.rows_with_email,
            "rows_without_email": self.rows_without_email,
            "invalid_emails": self.invalid_emails,
            "potential_duplicates": self.potential_duplicates,
            "sample_rows": self.sample_rows,
            "columns": self.columns,
            "mapping": self.mapping,
            "issues": self.issues,
        }


def _bounded_add(bucket: set[str], value: str) -> None:
    """Grow a tracking set only while it stays small enough to be cheap."""
    if value and len(bucket) < MAX_TRACKED_KEYS:
        bucket.add(value)


def _blocks(iterable, size: int):
    """Yield lists of at most ``size`` items — keeps memory bounded."""
    block: list = []
    for item in iterable:
        block.append(item)
        if len(block) >= size:
            yield block
            block = []
    if block:
        yield block


def _existing_keys(emails: set[str], domains: set[str]) -> tuple[set[str], set[str]]:
    """
    Which of these e-mails/domains already exist in the lead database.

    One query per batch (never one per row): the whole file can be checked with
    ``rows / LOOKUP_BATCH`` queries.
    """
    known_emails: set[str] = set()
    known_domains: set[str] = set()
    if emails:
        known_emails = set(
            Contact.objects.filter(normalized_email__in=emails)
            .values_list("normalized_email", flat=True)
            .distinct()
        )
    if domains:
        known_domains = set(
            Company.objects.filter(normalized_website__in=domains)
            .values_list("normalized_website", flat=True)
            .distinct()
        )
    return known_emails, known_domains


def analyze_file(
    path: str | Path,
    *,
    file_type: str,
    sheet: str | None = None,
    mapping: dict[str, str | None] | None = None,
    preview_rows: int = PREVIEW_ROWS,
) -> AnalysisResult:
    """
    Stream the file once and build the preview payload.

    ``mapping`` is optional: without it the columns are auto-detected. When the
    user re-maps a column the analysis is recomputed on the same pass so the
    duplicate counts reflect the new target fields.
    """
    # ``read_table`` consumes the header line and hands back the data rows only,
    # so the header is never counted as a record.
    headers, data_rows = read_table(path, file_type, sheet=sheet)
    if not headers:
        raise MappingError("The file has no header row.")

    matches = detect_mapping(headers)
    plan = build_plan(
        headers, mapping if mapping is not None else {m.column: m.field for m in matches}
    )

    result = AnalysisResult()
    result.columns = [match.as_dict() for match in matches]
    # ``{source column: system field | null}`` — the shape the UI edits and the
    # job stores. Unmapped columns are present with a null value.
    result.mapping = plan.column_mapping()

    seen_emails: set[str] = set()
    seen_domains: set[str] = set()

    # Rows are read (and checked against the database) in batches, so the
    # preview costs a couple of queries per thousand rows, not one per row.
    for block in _blocks(data_rows, LOOKUP_BATCH):
        records = [build_record(row.number, row.values, plan) for row in block]
        known_emails, known_domains = _existing_keys(
            {record.normalized_email for record in records if record.normalized_email},
            {record.domain for record in records if record.domain},
        )

        for row, record in zip(block, records, strict=True):
            result.total_rows += 1

            if record.normalized_email:
                result.rows_with_email += 1
            else:
                result.rows_without_email += 1

            if any(issue.message.startswith("Dropped invalid e-mail") for issue in record.issues):
                result.invalid_emails += 1
                if len(result.issues) < 20:
                    result.issues.append(record.issues[0].as_dict())

            # Duplicate? Either already in the database or repeated in the file.
            duplicate = bool(
                (
                    record.normalized_email
                    and (
                        record.normalized_email in known_emails
                        or record.normalized_email in seen_emails
                    )
                )
                or (
                    record.domain
                    and (record.domain in known_domains or record.domain in seen_domains)
                )
            )
            if duplicate:
                result.potential_duplicates += 1

            _bounded_add(seen_emails, record.normalized_email)
            _bounded_add(seen_domains, record.domain)

            if len(result.sample_rows) < preview_rows:
                result.sample_rows.append(
                    {
                        "row": row.number,
                        "values": row.values,
                        "company_name": record.company_name,
                        "contact_name": record.contact_name,
                        "email": record.email,
                        "phone": record.phone,
                        "notes": [issue.message for issue in record.issues],
                    }
                )

    return result


def describe_file(path: str | Path, file_type: str) -> dict:
    """File metadata for the upload card: sheets, encoding, delimiter."""
    info: dict = {"file_type": file_type, "sheets": [], "encoding": "", "delimiter": ""}
    if file_type == "xlsx":
        info["sheets"] = list(list_sheets(path, file_type))
    else:
        info["encoding"] = detect_encoding(path)
        info["delimiter"] = detect_delimiter(path, info["encoding"])
    return info
