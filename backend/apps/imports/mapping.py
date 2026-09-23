"""
Column detection for imported business datasets.

Real datasets never carry the column names we would choose: the same field
arrives as ``Business Name``, ``Company``, ``Organization`` or ``Business``, and
one file may use ``E-mail`` while the next uses ``Corporate Email``. The mapper
below turns arbitrary source headers into the system fields the lead database
understands, using three layers, in order:

1. **Normalized exact matching** — the header, reduced to lowercase alphanumeric
   tokens, equals a system field's key or label (``Company Name`` -> ``company``).
2. **Alias matching** — the header equals a curated alias, or contains one as a
   whole word/token (``Corporate Email`` -> ``email``, ``Web`` -> ``website``).
3. **Fuzzy matching** — :mod:`difflib` similarity on the normalized forms, used
   only when it is confident *and* clearly better than the runner-up, so
   unrelated columns are never silently mapped.

No AI/LLM is involved: the whole engine is deterministic and unit tested. Every
suggestion carries its method and confidence, so the preview UI can show what
was detected and the user can override any of it.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from dataclasses import field as dc_field
from difflib import SequenceMatcher

__all__ = [
    "AMBIGUITY_MARGIN",
    "FUZZY_THRESHOLD",
    "SYSTEM_FIELDS",
    "ColumnMatch",
    "SystemField",
    "detect_mapping",
    "field_by_key",
    "normalize_header",
    "system_fields_payload",
]


def normalize_header(value: str | None) -> str:
    """
    Canonical form used for every comparison: lowercase, accent-folded, with
    ``&`` spelled out and every run of punctuation collapsed to one space.

    ``"Business  Name (EN)"`` -> ``"business name en"``
    """
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class SystemField:
    """A field the importer can write to, plus the aliases that feed it."""

    key: str
    label: str
    description: str
    group: str  # "company" | "contact" | "meta"
    required: bool = False
    aliases: tuple[str, ...] = ()

    @property
    def normalized_aliases(self) -> tuple[str, ...]:
        return tuple(normalize_header(alias) for alias in self.aliases)


#: Fields the importer understands. ``lead_status``/``email_status``/``source``
#: carry through to the Lead row; everything else lands on Company or Contact.
SYSTEM_FIELDS: tuple[SystemField, ...] = (
    SystemField(
        key="company_name",
        label="Business name",
        description="Company / business name. Required — rows without it are rejected.",
        group="company",
        required=True,
        aliases=(
            "business name",
            "business",
            "company name",
            "company",
            "company title",
            "organisation",
            "organization",
            "organization name",
            "org name",
            "org",
            "account name",
            "account",
            "employer",
            "firm",
            "business title",
            "client name",
            "name of company",
            "corp name",
        ),
    ),
    SystemField(
        key="website",
        label="Website",
        description="Company website or domain; the domain is used as a dedup key.",
        group="company",
        aliases=(
            "website",
            "website url",
            "web site",
            "web",
            "url",
            "web address",
            "company website",
            "domain",
            "domain name",
            "site",
            "homepage",
            "link",
        ),
    ),
    SystemField(
        key="industry",
        label="Industry",
        description="Industry or sector of the business.",
        group="company",
        aliases=("industry", "sector", "vertical", "category", "business type", "sic", "naics"),
    ),
    SystemField(
        key="sub_industry",
        label="Sub industry",
        description="Narrower classification inside the industry.",
        group="company",
        aliases=("sub industry", "subindustry", "speciality", "specialty", "niche", "sub sector"),
    ),
    SystemField(
        key="employee_count",
        label="Employees",
        description="Head-count of the business (number of employees).",
        group="company",
        aliases=(
            "employee count",
            "employees",
            "employee size",
            "number of employees",
            "company size",
            "staff count",
            "headcount",
            "size",
        ),
    ),
    SystemField(
        key="company_phone",
        label="Company phone",
        description="Switchboard / main business phone number.",
        group="company",
        aliases=(
            "company phone",
            "business phone",
            "main phone",
            "office phone",
            "company telephone",
            "work phone",
        ),
    ),
    SystemField(
        key="street_address",
        label="Street address",
        description="Street line of the business address.",
        group="company",
        aliases=(
            "address",
            "street address",
            "street",
            "address line 1",
            "address 1",
            "street 1",
            "mailing address",
            "business address",
            "company address",
        ),
    ),
    SystemField(
        key="city",
        label="City",
        description="City or town.",
        group="company",
        aliases=("city", "town", "locality", "municipality"),
    ),
    SystemField(
        key="state",
        label="State",
        description="State, province or region.",
        group="company",
        aliases=("state", "province", "region", "state province", "territory"),
    ),
    SystemField(
        key="zip_code",
        label="ZIP code",
        description="Postal / ZIP code.",
        group="company",
        aliases=("zip", "zip code", "zipcode", "postal code", "postcode", "post code", "postal"),
    ),
    SystemField(
        key="country",
        label="Country",
        description="Country name or ISO code.",
        group="company",
        aliases=("country", "country name", "nation"),
    ),
    SystemField(
        key="contact_name",
        label="Contact name",
        description="Full name of the person; split into first / last name automatically.",
        group="contact",
        aliases=(
            "contact",
            "contact name",
            "contact person",
            "contact full name",
            "owner",
            "owner name",
            "business owner",
            "person",
            "person name",
            "full name",
            "name",
            "lead name",
            "decision maker",
            "proprietor",
            "principal",
        ),
    ),
    SystemField(
        key="first_name",
        label="First name",
        description="Given name of the contact.",
        group="contact",
        aliases=("first name", "firstname", "given name", "fname", "first"),
    ),
    SystemField(
        key="last_name",
        label="Last name",
        description="Family name of the contact.",
        group="contact",
        aliases=("last name", "lastname", "surname", "family name", "lname", "second name"),
    ),
    SystemField(
        key="job_title",
        label="Job title",
        description="Role or position of the contact.",
        group="contact",
        aliases=(
            "job title",
            "title",
            "position",
            "role",
            "designation",
            "job position",
            "occupation",
            "contact title",
        ),
    ),
    SystemField(
        key="email",
        label="E-mail",
        description="Primary e-mail address of the contact. Syntax is validated.",
        group="contact",
        aliases=(
            "email",
            "e mail",
            "email address",
            "e mail address",
            "corporate email",
            "work email",
            "business email",
            "primary email",
            "email id",
            "mail",
            "contact email",
            "email1",
            "email address 1",
        ),
    ),
    SystemField(
        key="phone",
        label="Phone",
        description="Primary phone number — stored on the company and, when a person is present, the contact.",
        group="contact",
        aliases=(
            "phone",
            "phone number",
            "telephone",
            "tel",
            "phone no",
            "contact phone",
            "contact number",
            "mobile",
            "mobile number",
            "mobile phone",
            "cell",
            "cell phone",
            "cellphone",
            "whatsapp",
            "whatsapp number",
            "landline",
            "landline number",
            "office phone",
        ),
    ),
    SystemField(
        key="contact_phone",
        label="Contact phone",
        description="Phone number of the person only (not the company switchboard).",
        group="contact",
        aliases=("direct phone", "direct dial", "personal phone", "person phone", "direct line"),
    ),
    SystemField(
        key="linkedin_url",
        label="LinkedIn",
        description="LinkedIn profile URL (kept with the row; not stored on the lead yet).",
        group="meta",
        aliases=("linkedin", "linkedin url", "linkedin profile", "linked in"),
    ),
    SystemField(
        key="source",
        label="Source",
        description="Where the record came from (dataset name, list provider, …).",
        group="meta",
        aliases=("source", "data source", "lead source", "list source", "provider", "vendor"),
    ),
)

FIELD_BY_KEY: dict[str, SystemField] = {item.key: item for item in SYSTEM_FIELDS}

#: Similarity needed before a fuzzy match is trusted.
FUZZY_THRESHOLD = 0.84
#: How far ahead of the runner-up a fuzzy match must be to be unambiguous.
AMBIGUITY_MARGIN = 0.05

#: Single words that are too generic to match inside a longer header. They still
#: match when the header *is* that word ("Email" -> email), but "ID" or "Name"
#: must not be pulled into a field just because an alias mentions them.
WEAK_TOKENS = frozenset(
    {
        "a",
        "address",
        "cell",
        "code",
        "col",
        "column",
        "data",
        "desc",
        "description",
        "e",
        "fax",
        "field",
        "id",
        "info",
        "link",
        "m",
        "mail",
        "n",
        "name",
        "no",
        "note",
        "notes",
        "number",
        "other",
        "site",
        "size",
        "source",
        "tel",
        "telephone",
        "text",
        "type",
        "unnamed",
        "url",
        "value",
        "web",
        "x",
    }
)

#: Headers that imply the number is a mobile, so ``phone_type`` can be set.
MOBILE_ALIASES = frozenset(
    {
        "mobile",
        "mobile number",
        "mobile phone",
        "cell",
        "cell phone",
        "cellphone",
        "whatsapp",
        "whatsapp number",
    }
)

#: Keyword → ``Contact.PhoneType`` for columns that name the kind of line.
PHONE_TYPE_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("mobile", "MOBILE"),
    ("cell", "MOBILE"),
    ("whatsapp", "MOBILE"),
    ("landline", "LANDLINE"),
    ("direct", "OFFICE"),
    ("office", "OFFICE"),
    ("work", "OFFICE"),
    ("business", "OFFICE"),
    ("main", "OFFICE"),
    ("switchboard", "OFFICE"),
)


def phone_type_for_header(header_key: str) -> str:
    """
    Guess the phone type from the column name: ``"Cell Phone"`` → ``MOBILE``.

    Returns an empty string when the header says nothing about the line type.
    """
    for keyword, phone_type in PHONE_TYPE_KEYWORDS:
        if keyword in header_key.split():
            return phone_type
    return ""


#: Header fragments that make a column useless for dedup or import.
GENERIC_HEADERS = frozenset({"", "column", "field", "unnamed", "n a", "na", "none", "null"})


@dataclass
class ColumnMatch:
    """What the mapper decided for one source column."""

    column: str
    field: str | None = None
    label: str = ""
    confidence: float = 0.0
    method: str = "none"  # exact | alias | fuzzy | none
    hint: str = ""
    matched_on: str = ""  # alias/label that produced the match (for the UI)
    candidates: list[tuple[str, float]] = dc_field(default_factory=list)

    @property
    def matched(self) -> bool:
        return self.field is not None

    def as_dict(self) -> dict:
        return {
            "column": self.column,
            "field": self.field,
            "label": self.label,
            "confidence": round(self.confidence, 3),
            "method": self.method,
            "hint": self.hint,
            "matched_on": self.matched_on,
        }


def field_by_key(key: str) -> SystemField | None:
    return FIELD_BY_KEY.get(key)


def system_fields_payload() -> list[dict]:
    """Catalog served to the mapping UI (dropdown options + tooltips)."""
    return [
        {
            "key": item.key,
            "label": item.label,
            "description": item.description,
            "group": item.group,
            "required": item.required,
            "aliases": list(item.aliases),
        }
        for item in SYSTEM_FIELDS
    ]


def _token_sort_ratio(left: str, right: str) -> float:
    """Compare the two strings with their tokens sorted (order-insensitive)."""
    return SequenceMatcher(
        None, " ".join(sorted(left.split())), " ".join(sorted(right.split()))
    ).ratio()


def _containment_score(header_key: str, form_key: str) -> float:
    """
    Score when one side's tokens are a strict subset of the other's.

    ``"primary contact"`` ⊃ ``"contact"`` scores ~0.92; a subset made of a single
    generic word ("id", "name", "web") scores 0 — those only match exactly, so
    "ID" is never treated as an e-mail column.
    """
    header_tokens, form_tokens = header_key.split(), form_key.split()
    if not header_tokens or not form_tokens or len(header_tokens) == len(form_tokens):
        return 0.0

    smaller, larger = (
        (header_tokens, form_tokens)
        if len(header_tokens) < len(form_tokens)
        else (form_tokens, header_tokens)
    )
    if not set(smaller) <= set(larger):
        return 0.0
    if len(smaller) == 1 and smaller[0] in WEAK_TOKENS:
        return 0.0
    return 0.88 + 0.07 * (len(smaller) / len(larger))


def _similarity(left: str, right: str) -> float:
    """Blend raw sequence similarity with order-insensitive matching."""
    if not left or not right:
        return 0.0
    return max(
        SequenceMatcher(None, left, right).ratio(),
        _token_sort_ratio(left, right),
        _containment_score(left, right),
    )


#: Trailing tokens that mark a column as a record identifier rather than data.
IDENTIFIER_TOKENS = frozenset(
    {
        "id",
        "no",
        "number",
        "code",
        "key",
        "ref",
        "reference",
        "index",
        "row",
        "rec",
        "record",
        "uuid",
        "guid",
    }
)


def _looks_like_row_identifier(header_key: str, matched_form: str) -> bool:
    """
    ``"Company ID"`` is a record key, not the company name.

    A trailing identifier token only counts against the match when the matched
    form/alias does not carry it itself ("Zip Code" keeps ``code`` legitimately).
    """
    header_tokens = header_key.split()
    if len(header_tokens) < 2:
        return False
    last = header_tokens[-1]
    return last in IDENTIFIER_TOKENS and last not in matched_form.split()


def _candidates(header_key: str) -> list[tuple[str, float]]:
    """Score every system field against a normalized header, best first."""
    scored: list[tuple[str, float]] = []
    for item in SYSTEM_FIELDS:
        forms = {item.key, normalize_header(item.label), *item.normalized_aliases}
        best = max((_similarity(header_key, form) for form in forms if form), default=0.0)
        scored.append((item.key, best))
    scored.sort(key=lambda pair: (-pair[1], pair[0]))
    return scored


def _best_form(header_key: str, item: SystemField) -> str:
    """The alias/label that produced the best score — used for reporting."""
    forms = [item.key, normalize_header(item.label), *item.normalized_aliases]
    return max(
        (form for form in forms if form), key=lambda form: _similarity(header_key, form), default=""
    )


def _match_exact(header_key: str) -> SystemField | None:
    for item in SYSTEM_FIELDS:
        if header_key == item.key or header_key == normalize_header(item.label):
            return item
    return None


def _match_alias(header_key: str) -> tuple[SystemField, float] | None:
    """
    Whole-string alias first, then whole-token alias ("corporate email" → email).

    Token containment is scored slightly lower than an exact alias so a literal
    match always wins when two fields are plausible.
    """
    partial: tuple[SystemField, float] | None = None

    for item in SYSTEM_FIELDS:
        for alias in item.normalized_aliases:
            if not alias:
                continue
            if header_key == alias:
                return item, 1.0
            alias_tokens = alias.split()
            # A lone generic word ("name", "id", "web") never matches inside a
            # longer header — otherwise "Busines Name" would look like a contact.
            if len(alias_tokens) == 1 and alias_tokens[0] in WEAK_TOKENS:
                continue
            if set(alias_tokens) <= set(header_key.split()):
                score = 0.9 + 0.05 * (len(alias_tokens) / len(header_key.split()))
                if partial is None or score > partial[1]:
                    partial = (item, min(score, 0.95))
    return partial


def _match_fuzzy(header_key: str) -> tuple[SystemField, float] | None:
    scored = _candidates(header_key)
    if not scored:
        return None

    best_key, best_score = scored[0]
    runner_up = scored[1][1] if len(scored) > 1 else 0.0
    if best_score < FUZZY_THRESHOLD or best_score - runner_up < AMBIGUITY_MARGIN:
        return None

    item = FIELD_BY_KEY.get(best_key)
    return (item, best_score) if item else None


def detect_field(column: str) -> ColumnMatch:
    """Detect the system field for a single source column."""
    match = ColumnMatch(column=column)
    header_key = normalize_header(column)

    if not header_key or header_key in GENERIC_HEADERS or header_key.startswith("column "):
        match.candidates = _candidates(header_key)[:3]
        return match

    detected = _match_exact(header_key)
    if detected:
        match.field, match.confidence, match.method = detected.key, 1.0, "exact"
        match.matched_on = header_key
    else:
        aliased = _match_alias(header_key)
        if aliased:
            match.field, match.confidence, match.method = aliased[0].key, aliased[1], "alias"
            match.matched_on = _best_form(header_key, aliased[0])
        else:
            fuzzy = _match_fuzzy(header_key)
            if fuzzy:
                match.field, match.confidence, match.method = fuzzy[0].key, fuzzy[1], "fuzzy"
                match.matched_on = _best_form(header_key, fuzzy[0])

    # Guard: "Company ID", "Row No", "Record Ref" are keys, not names/addresses.
    if match.field and _looks_like_row_identifier(header_key, match.matched_on):
        match.candidates = [(match.field, round(match.confidence, 3)), *match.candidates][:3]
        match.field, match.label, match.confidence, match.method = None, "", 0.0, "none"
        match.matched_on = ""

    if match.field:
        match.label = FIELD_BY_KEY[match.field].label
        if match.field in {"phone", "contact_phone", "company_phone"}:
            match.hint = phone_type_for_header(header_key)

    match.candidates = [(key, round(score, 3)) for key, score in _candidates(header_key)[:3]]
    return match


def detect_mapping(headers: list[str]) -> list[ColumnMatch]:
    """
    Detect a field for every header, then resolve collisions.

    One system field can only be fed by one column: when several columns claim
    the same field the most confident (then left-most) one keeps it and the
    others fall back to "unmapped" so the user can decide in the preview.
    """
    matches = [detect_field(header) for header in headers]

    winners: dict[str, ColumnMatch] = {}
    for match in matches:
        if not match.matched:
            continue
        current = winners.get(match.field)  # type: ignore[index]
        if current is None or match.confidence > current.confidence:
            winners[match.field] = match  # type: ignore[index]

    for match in matches:
        if match.matched and winners.get(match.field) is not match:  # type: ignore[arg-type]
            match.candidates = [(match.field, match.confidence), *match.candidates][:3]  # type: ignore[list-item]
            match.field, match.label, match.confidence, match.method, match.hint = (
                None,
                "",
                0.0,
                "none",
                "",
            )

    return matches


def mapping_dict(matches: list[ColumnMatch]) -> dict[str, str | None]:
    """``{source column: system field}`` — the shape stored on ``ImportJob``."""
    return {match.column: match.field for match in matches}
