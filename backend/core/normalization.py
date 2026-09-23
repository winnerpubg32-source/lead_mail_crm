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
    "address_key",
    "normalize_address",
    "normalize_contact_name",
    "normalize_company_name",
    "normalize_domain",
    "normalize_email",
    "normalize_phone",
    "normalize_whitespace",
    "normalize_name_case",
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


# Common US/UK street-type abbreviations that appear in addresses. We normalize
# these to a canonical short form so "123 Main Street" and "123 Main St" match.
_ADDRESS_ABBREV = {
    "avenue": "ave",
    "ave": "ave",
    "boulevard": "blvd",
    "blvd": "blvd",
    "circle": "cir",
    "cir": "cir",
    "court": "ct",
    "ct": "ct",
    "drive": "dr",
    "dr": "dr",
    "expressway": "expy",
    "freeway": "fwy",
    "highway": "hwy",
    "lane": "ln",
    "ln": "ln",
    "parkway": "pkwy",
    "place": "pl",
    "pl": "pl",
    "road": "rd",
    "rd": "rd",
    "route": "rte",
    "square": "sq",
    "sq": "sq",
    "street": "st",
    "st": "st",
    "suite": "ste",
    "ste": "ste",
    "terrace": "ter",
    "ter": "ter",
    "trail": "trl",
    "way": "way",
    "north": "n",
    "south": "s",
    "east": "e",
    "west": "w",
    "northeast": "ne",
    "northwest": "nw",
    "southeast": "se",
    "southwest": "sw",
    "ne": "ne",
    "nw": "nw",
    "se": "se",
    "sw": "sw",
    "n": "n",
    "s": "s",
    "e": "e",
    "w": "w",
    "apt": "apt",
    "apartment": "apt",
    "unit": "unit",
    "floor": "fl",
    "fl": "fl",
    "#": "",
}

_US_STATE_ABBREV = {
    "alabama": "al",
    "alaska": "ak",
    "arizona": "az",
    "arkansas": "ar",
    "california": "ca",
    "colorado": "co",
    "connecticut": "ct",
    "delaware": "de",
    "florida": "fl",
    "georgia": "ga",
    "hawaii": "hi",
    "idaho": "id",
    "illinois": "il",
    "indiana": "in",
    "iowa": "ia",
    "kansas": "ks",
    "kentucky": "ky",
    "louisiana": "la",
    "maine": "me",
    "maryland": "md",
    "massachusetts": "ma",
    "michigan": "mi",
    "minnesota": "mn",
    "mississippi": "ms",
    "missouri": "mo",
    "montana": "mt",
    "nebraska": "ne",
    "nevada": "nv",
    "newhampshire": "nh",
    "newjersey": "nj",
    "newmexico": "nm",
    "newyork": "ny",
    "northcarolina": "nc",
    "northdakota": "nd",
    "ohio": "oh",
    "oklahoma": "ok",
    "oregon": "or",
    "pennsylvania": "pa",
    "rhodeisland": "ri",
    "southcarolina": "sc",
    "southdakota": "sd",
    "tennessee": "tn",
    "texas": "tx",
    "utah": "ut",
    "vermont": "vt",
    "virginia": "va",
    "washington": "wa",
    "westvirginia": "wv",
    "wisconsin": "wi",
    "wyoming": "wy",
    "districtofcolumbia": "dc",
}


def normalize_address(
    street: str | None = None,
    city: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
    country: str | None = None,
) -> str:
    """
    Canonical street address used for matching.

    Lowercases, strips accents, collapses punctuation, shortens common
    street-type abbreviations, and normalises US state names to two-letter
    codes. Does not invent missing parts.
    """
    # Normalize state first so "Ohio" -> "OH" before tokenisation.
    norm_state = normalize_state(state) if state else ""
    parts = [
        normalize_whitespace(street),
        normalize_whitespace(city),
        norm_state,
        normalize_whitespace(zip_code),
        normalize_whitespace(country),
    ]
    combined = ", ".join(p for p in parts if p)
    if not combined:
        return ""
    text = _strip_accents(combined).lower()
    text = text.replace("&", " and ")
    text = _NON_ALNUM.sub(" ", text)
    tokens: list[str] = []
    for token in text.split():
        # State abbreviation after normalization is already short; check if
        # expanded form snuck in via concatenated tokens.
        canonical = _ADDRESS_ABBREV.get(token, token)
        if not canonical:
            continue
        # Also normalize state tokens: "ohio" -> "oh"
        canonical = _US_STATE_ABBREV.get(canonical, canonical)
        tokens.append(canonical)
    return " ".join(tokens)


def address_key(
    street: str | None = None,
    city: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
) -> str:
    """Tight alphanumeric key for address matching — city+state+street."""
    return normalize_address(street, city, state, zip_code).replace(" ", "")


_NAME_TITLES = {"dr", "mr", "mrs", "ms", "miss", "prof", "sir", "hon", "rev"}


def normalize_contact_name(first_name: str | None, last_name: str | None) -> str:
    """
    Canonical contact name used for matching.

    Lowercases, collapses whitespace, strips accents, and drops titles/punctuation.
    ``" Dr.  Maria  O'Brien "`` and ``"maria obrien"`` become comparable.
    """
    full = build_full_name(first_name, last_name)
    if not full:
        return ""
    text = _strip_accents(full).lower()
    text = _NON_ALNUM.sub(" ", text)
    tokens = [t for t in text.split() if t not in _NAME_TITLES]
    return normalize_whitespace(" ".join(tokens))


def normalize_name_case(value: str | None) -> str:
    """
    Apply a light title-case normalization so "jane smith" becomes "Jane Smith"
    while preserving internal capitals like "McDonald" or "O'Brien". This is
    cosmetic only (never stored as the dedup key) and never invents anything.
    """
    text = normalize_whitespace(value)
    if not text:
        return ""
    # Title-case but keep spacing; preserve obvious mixed-case words.
    return " ".join(word[:1].upper() + word[1:] for word in text.split())


def normalize_state(value: str | None) -> str:
    """Return a canonical two-letter US state abbreviation when we can."""
    text = normalize_whitespace(value)
    if not text:
        return ""
    key = re.sub(r"[^a-z]", "", _strip_accents(text).lower())
    if key in _US_STATE_ABBREV:
        return _US_STATE_ABBREV[key].upper()
    return text.upper() if len(key) == 2 else text
