"""
Turn a physical file row into a normalized record.

Both the **preview** (which only counts and samples) and the **importer** (which
writes to the database) go through :func:`build_record`, so what the user sees in
the preview is exactly what the run will do — no second implementation, no
drift between the two.

Rules applied here, straight from the brief:

* e-mail syntax is validated and broken addresses are **dropped**, never fixed;
* phone numbers, websites, company names, person names and addresses are
  normalized through :mod:`core.normalization`;
* a missing e-mail is *not* a problem — the record is still stored;
* a row without a business name cannot be attached to anything and is rejected.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field as dc_field

from core.normalization import (
    build_full_name,
    normalize_company_name,
    normalize_domain,
    normalize_email,
    normalize_phone,
    normalize_whitespace,
    split_full_name,
)

__all__ = [
    "EMAIL_PATTERN",
    "Record",
    "RowIssue",
    "build_plan",
    "build_record",
    "is_valid_email",
    "parse_employee_count",
]

#: Pragmatic syntax check — one ``@``, a dotted domain, no spaces. Anything that
#: fails is dropped (the brief forbids inventing or repairing addresses).
EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
    r"@(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}$"
)

#: Fields whose values describe the company, the person, or rows metadata.
COMPANY_FIELDS = (
    "company_name",
    "website",
    "industry",
    "sub_industry",
    "employee_count",
    "company_phone",
    "street_address",
    "city",
    "state",
    "zip_code",
    "country",
)
CONTACT_FIELDS = (
    "contact_name",
    "first_name",
    "last_name",
    "job_title",
    "email",
    "phone",
    "contact_phone",
)
META_FIELDS = ("linkedin_url", "source")

TEXT_LIMITS = {
    "company_name": 255,
    "industry": 150,
    "sub_industry": 150,
    "street_address": 255,
    "city": 120,
    "state": 120,
    "zip_code": 20,
    "country": 120,
    "job_title": 180,
    "first_name": 120,
    "last_name": 120,
    "source": 120,
}


def is_valid_email(value: str) -> bool:
    """True when the address passes both normalization and the syntax pattern."""
    if not value or not EMAIL_PATTERN.match(value):
        return False
    local, _, domain = value.rpartition("@")
    return bool(normalize_email(value)) and local.strip(". ") != "" and "." in domain


def parse_employee_count(value: str) -> int | None:
    """
    Read a head-count out of the usual messy shapes.

    ``"1,200"`` → 1200 · ``"50-100"`` → 50 · ``"250+"`` → 250 · ``"n/a"`` → None
    """
    text = normalize_whitespace(value)
    if not text:
        return None
    match = re.search(r"\d[\d,.\s]*", text)
    if not match:
        return None
    digits = re.sub(r"[^\d]", "", match.group(0))
    if not digits:
        return None
    return max(0, min(int(digits), 10_000_000))


@dataclass(frozen=True)
class RowIssue:
    """One problem found while reading a row."""

    row: int
    level: str  # "warning" | "invalid" | "error"
    message: str
    column: str = ""

    def as_dict(self) -> dict:
        return {
            "row": self.row,
            "level": self.level,
            "message": self.message,
            "column": self.column,
        }


@dataclass
class Record:
    """Normalized content of one row (all strings are safe to store)."""

    row: int
    company_name: str = ""
    normalized_name: str = ""
    website: str = ""
    domain: str = ""
    industry: str = ""
    sub_industry: str = ""
    employee_count: int | None = None

    company_phone: str = ""
    street_address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = ""

    contact_name: str = ""
    first_name: str = ""
    last_name: str = ""
    job_title: str = ""
    email: str = ""
    normalized_email: str = ""
    phone: str = ""
    contact_phone: str = ""
    phone_type: str = "UNKNOWN"

    linkedin_url: str = ""
    source: str = ""
    issues: list[RowIssue] = dc_field(default_factory=list)

    # --- Derived --------------------------------------------------------------
    @property
    def has_company(self) -> bool:
        return bool(self.company_name)

    @property
    def has_person(self) -> bool:
        """A named human being (as opposed to a generic mailbox)."""
        return bool(self.contact_name or self.first_name or self.last_name)

    @property
    def has_email(self) -> bool:
        return bool(self.normalized_email)

    @property
    def is_usable(self) -> bool:
        """Without a company name the row cannot be attached to anything."""
        return self.has_company

    @property
    def needs_contact(self) -> bool:
        """Create a Contact row when there is any person data or an address."""
        return self.has_person or self.has_email

    @property
    def contact_key(self) -> str:
        """Stable identity of the contact inside its company."""
        if self.normalized_email:
            return f"email:{self.normalized_email}"
        return f"name:{normalize_company_name(self.contact_name)}" if self.contact_name else ""

    @property
    def company_key(self) -> str:
        """Preferred company match key: domain first, then the normalized name."""
        if self.domain:
            return f"domain:{self.domain}"
        return f"name:{self.normalized_name}"

    def summary(self) -> str:
        """``"Northwind Logistics — Marcus Whitfield <m@x.com>"`` for the preview."""
        person = self.contact_name or self.email
        return f"{self.company_name} — {person}" if person else self.company_name


@dataclass(frozen=True)
class Plan:
    """Resolved column plan: which system field reads which column index."""

    #: ``{field: (column index, source header, hint)}``
    fields: dict[str, tuple[int, str, str]]
    headers: tuple[str, ...]

    def has(self, name: str) -> bool:
        return name in self.fields

    def value(self, name: str, values: list[str]) -> str:
        entry = self.fields.get(name)
        if not entry:
            return ""
        index = entry[0]
        return values[index] if index < len(values) else ""

    def column_mapping(self) -> dict[str, str | None]:
        """
        ``{source column: system field | None}`` — the canonical mapping shape.

        It is what the job stores, what the preview table edits and what the API
        returns; every column of the file is present, unmapped ones as ``None``.
        """
        mapping: dict[str, str | None] = dict.fromkeys(self.headers)
        for field, (_index, column, _hint) in self.fields.items():
            mapping[column] = field
        return mapping

    def mergeable(self) -> dict[str, str]:
        """``{system field: source column}`` — only the mapped fields."""
        return {name: entry[1] for name, entry in self.fields.items()}


class MappingError(ValueError):
    """Raised when a mapping cannot be used for an import run."""


def build_plan(headers: list[str], mapping: dict[str, str | None]) -> Plan:
    """
    Resolve ``{source column: system field}`` into column indexes.

    Unmapped columns are ignored, unknown system fields are rejected and a
    second column claiming an already-mapped field is dropped (the UI prevents
    this, the API must not trust it).
    """
    from apps.imports.mapping import FIELD_BY_KEY, detect_mapping

    if not mapping:
        mapping = {match.column: match.field for match in detect_mapping(headers)}

    index_of = {header: index for index, header in enumerate(headers)}
    hints = {match.column: match.hint for match in detect_mapping(headers)}
    fields: dict[str, tuple[int, str, str]] = {}

    for column, target in mapping.items():
        if not target:
            continue
        if target not in FIELD_BY_KEY:
            raise MappingError(f"Unknown system field: {target}")
        if column not in index_of:
            continue
        if target in fields:
            continue
        fields[target] = (index_of[column], column, hints.get(column, ""))

    return Plan(fields=fields, headers=tuple(headers))


def _clean(value: str, limit: int | None = None) -> str:
    text = normalize_whitespace(value)
    return text[:limit] if limit else text


def build_record(row_number: int, values: list[str], plan: Plan) -> Record:
    """Normalize one row; never raises — problems are recorded as issues."""
    record = Record(row=row_number)
    take = lambda name: _clean(plan.value(name, values), TEXT_LIMITS.get(name))  # noqa: E731

    if plan.headers and len(values) != len(plan.headers):
        # Unquoted commas are the classic cause: the row is still read, but the
        # columns may be shifted, so the preview must say so.
        record.issues.append(
            RowIssue(
                row=row_number,
                level="warning",
                message=(
                    f"Row has {len(values)} values but the header has {len(plan.headers)} columns"
                    " — check the file for unquoted separators."
                ),
            )
        )

    # --- Company --------------------------------------------------------------
    record.company_name = take("company_name")
    record.website = _clean(plan.value("website", values), 500)
    record.industry = take("industry")
    record.sub_industry = take("sub_industry")
    record.employee_count = parse_employee_count(plan.value("employee_count", values))
    record.company_phone = _clean(plan.value("company_phone", values), 50)
    record.street_address = take("street_address")
    record.city = take("city")
    record.state = take("state")
    record.zip_code = take("zip_code")
    record.country = take("country") or "United States"
    record.source = take("source")

    # --- Person ---------------------------------------------------------------
    raw_contact = _clean(plan.value("contact_name", values), 255)
    first = take("first_name")
    last = take("last_name")

    if first or last:
        record.first_name, record.last_name = first, last
        record.contact_name = build_full_name(first, last)
    elif raw_contact:
        record.first_name, record.last_name = split_full_name(raw_contact)
        record.contact_name = raw_contact

    record.job_title = take("job_title")

    # --- E-mail ---------------------------------------------------------------
    raw_email = _clean(plan.value("email", values), 320)
    if raw_email:
        candidate = normalize_email(raw_email)
        if is_valid_email(candidate):
            record.email = candidate
            record.normalized_email = candidate
        else:
            record.issues.append(
                RowIssue(
                    row=row_number,
                    level="warning",
                    message=f"Dropped invalid e-mail address: {raw_email[:80]}",
                    column=plan.fields.get("email", (0, "", ""))[1],
                )
            )

    # --- Phones ---------------------------------------------------------------
    primary_phone = _clean(plan.value("phone", values), 50)
    direct_phone = _clean(plan.value("contact_phone", values), 50)
    record.contact_phone = normalize_phone(direct_phone or primary_phone)
    record.company_phone = normalize_phone(record.company_phone or primary_phone)
    record.phone = record.contact_phone or record.company_phone

    hint = (
        plan.fields.get("contact_phone", (0, "", ""))[2] or plan.fields.get("phone", (0, "", ""))[2]
    )
    record.phone_type = hint or "UNKNOWN"

    # --- Normalized keys ------------------------------------------------------
    # Names made only of legal suffixes ("Inc.") normalize to nothing; falling
    # back to the raw lowercase name keeps every row its own company instead of
    # merging unrelated businesses into one bucket.
    record.normalized_name = (
        normalize_company_name(record.company_name) or record.company_name.lower()[:255]
    )
    record.domain = normalize_domain(record.website)
    record.linkedin_url = _clean(plan.value("linkedin_url", values), 255)

    return record
