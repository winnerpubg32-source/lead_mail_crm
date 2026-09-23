"""
Normalisation helpers shared by the ingest and dedup layers.

Imported business datasets are messy: the same company arrives as
"Northwind Logistics, Inc." and "northwind logistics llc", websites as
"https://www.NorthwindLogistics.com/contact" and "northwindlogistics.com", and
e-mail addresses with mixed casing. Every model in the lead database stores a
normalised twin of the fields that matter for matching, so dedup rules (Phase 3)
can rely on a stable canonical form instead of ad-hoc string comparisons.

Nothing here touches the database — these are pure functions and are unit
tested in ``core.tests.test_normalization``.
"""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlsplit

__all__ = [
    "build_full_name",
    "company_name_key",
    "normalize_company_name",
    "normalize_domain",
    "normalize_email",
    "normalize_phone",
    "normalize_whitespace",
    "split_full_name",
]

# Legal entity suffixes/prefixes that carry no matching value.
LEGAL_SUFFIXES = {
    "ag",
    "as",
    "bv",
    "co",
    "company",
    "corp",
    "corporation",
    "gmbh",
    "group",
    "holding",
    "holdings",
    "inc",
    "incorporated",
    "limited",
    "llc",
    "llp",
    "lp",
    "ltd",
    "nv",
    "oy",
    "plc",
    "private",
    "pte",
    "pty",
    "pvt",
    "sa",
    "sarl",
    "spa",
    "srl",
}

# Words that stay lowercase between two capitalised tokens ("Bank of America").
MINOR_WORDS = {"a", "an", "and", "at", "by", "for", "in", "of", "on", "or", "the", "to"}

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_EMAIL_LOCAL_KEEP = re.compile(r"[^a-zA-Z0-9.!#$%&'*+/=?^_`{|}~\-]")
_EMAIL_DOMAIN_KEEP = re.compile(r"[^a-zA-Z0-9.\-]")


def normalize_whitespace(value: str | None) -> str:
    """Collapse every run of whitespace and trim the result."""
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _strip_accents(value: str) -> str:
    """Fold accents so "Café" and "Cafe" match."""
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def normalize_company_name(value: str | None) -> str:
    """
    Canonical company name used for matching.

    ``"Northwind Logistics, Inc."`` -> ``"northwind logistics"``
    ``"ACME  LLC"``                -> ``"acme"``
    """
    text = normalize_whitespace(value)
    if not text:
        return ""

    text = _strip_accents(text).lower()
    text = text.replace("&", " and ")
    text = _NON_ALNUM.sub(" ", text)
    tokens = [token for token in text.split() if token not in LEGAL_SUFFIXES]
    # "Limited" style suffixes only make sense at the end, but removing them
    # anywhere is safer than keeping them: a false merge is caught in review,
    # a false split silently duplicates the database.
    return " ".join(tokens)


def company_name_key(value: str | None) -> str:
    """Tight key (no spaces) used for fuzzy duplicate detection."""
    return normalize_company_name(value).replace(" ", "")


def normalize_domain(value: str | None) -> str:
    """
    Extract the bare registrable host from a website, URL or e-mail domain.

    ``"https://www.NorthwindLogistics.com/about?utm=1"`` -> ``"northwindlogistics.com"``
    ``"NorthwindLogistics.COM/"``                        -> ``"northwindlogistics.com"``
    """
    text = normalize_whitespace(value)
    if not text:
        return ""

    text = text.lower()

    # A bare domain ("acme.com") has no scheme; "//" makes urlsplit treat the
    # first segment as the netloc instead of a path.
    if "//" not in text.split("?", 1)[0][:8]:
        text = f"//{text}"

    host = urlsplit(text).netloc or urlsplit(text).path
    host = host.split("@")[-1]  # strip userinfo from e-mail-style input
    host = host.split(":")[0]  # strip port
    host = host.strip().strip(".")

    if host.startswith("www."):
        host = host[4:]

    return host


def normalize_email(value: str | None) -> str:
    """Lowercase, trim and strip characters that never appear in a valid address."""
    text = normalize_whitespace(value)
    if not text or "@" not in text:
        return ""

    local, _, domain = text.rpartition("@")
    local = _EMAIL_LOCAL_KEEP.sub("", local)
    domain = _EMAIL_DOMAIN_KEEP.sub("", domain.lower())

    if not local or not domain or "." not in domain:
        return ""

    return f"{local.lower()}@{domain}"


def normalize_phone(value: str | None) -> str:
    """
    Digits only, keeping a leading ``+`` for international numbers.

    ``"(614) 555-0142"`` -> ``"6145550142"`` · ``"+1 614 555 0142"`` -> ``"+16145550142"``
    """
    text = normalize_whitespace(value)
    if not text:
        return ""

    digits = re.sub(r"\D", "", text)
    if not digits:
        return ""

    return f"+{digits}" if text.strip().startswith("+") else digits


def build_full_name(first_name: str | None, last_name: str | None) -> str:
    """Join the name parts into the denormalised ``full_name`` column."""
    return normalize_whitespace(f"{first_name or ''} {last_name or ''}")


def split_full_name(full_name: str | None) -> tuple[str, str]:
    """
    Best-effort split of a single imported name field.

    ``"Dr. Elena Ruiz"`` -> ``("Elena", "Ruiz")`` — titles are dropped, and a
    single token becomes the first name.
    """
    text = normalize_whitespace(full_name)
    if not text:
        return "", ""

    tokens = [
        token
        for token in text.split()
        if token.rstrip(".").lower() not in {"dr", "mr", "mrs", "ms", "miss", "prof", "sir"}
    ]
    if not tokens:
        return "", ""
    if len(tokens) == 1:
        return tokens[0], ""
    return " ".join(tokens[:-1]), tokens[-1]
