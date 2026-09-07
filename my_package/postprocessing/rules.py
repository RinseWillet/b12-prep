"""Deterministic post-processing: normalization, ISIN validation, and sentinel/confidence rules."""
import re
from datetime import date, datetime
from typing import Any, Dict, Optional

from my_package.models.prospectus import ExtractedField, ProspectusFields

ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")
_LETTER_VALUES = {chr(ord("A") + i): str(10 + i) for i in range(26)}
DATE_FORMATS = ["%d %B %Y", "%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"]
CURRENCY_SYMBOLS = {"$": "USD", "\u20ac": "EUR", "\u00a3": "GBP", "\u00a5": "JPY"}


# Validate an ISIN's check digit using the ISO 6166 (Luhn-style) algorithm (see also https://en.wikipedia.org/wiki/International_Securities_Identification_Number#Check-digit  )
def isin_checksum_valid(isin: Optional[Any]) -> bool:
    """Validate an ISIN's check digit using the ISO 6166 (Luhn-style) algorithm."""
    if not isin or not isinstance(isin, str) or not ISIN_PATTERN.match(isin):
        return False
    digits = "".join(_LETTER_VALUES.get(ch, ch) for ch in isin.upper())
    total = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        n = int(d)
        if i % 2 == parity:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0

# Normalize a date string into a datetime.date object. Returns None if parsing fails.
def normalize_date(raw: Optional[Any]) -> Optional[date]:
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None

# Normalize a currency string into a 3-letter ISO currency code. Returns None if parsing fails.
def normalize_currency(raw: Optional[Any]) -> Optional[str]:
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    if raw in CURRENCY_SYMBOLS:
        return CURRENCY_SYMBOLS[raw]
    upper = raw.upper()
    return upper if CURRENCY_PATTERN.match(upper) else None


# Normalize a numeric amount string into a float. Returns None if parsing fails.
def normalize_amount(raw: Optional[Any]) -> Optional[float]:
    if raw is None or raw == "":
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    cleaned = raw.replace(",", "").replace(" ", "")
    try:
        return float(cleaned)
    except ValueError:
        return None

# Postprocess a raw extraction dictionary into a ProspectusFields object, normalizing and validating fields.
def postprocess(raw: Dict[str, Any], method: str = "stub") -> ProspectusFields:
    """Normalize, validate, and attach confidence/sentinel metadata to a raw extraction dict."""

    def field(value: Any, confidence: float) -> ExtractedField:
        return ExtractedField(value=value, confidence=confidence, extraction_method=method)

    isin_value = raw.get("isin")
    isin_confidence = 0.9 if isin_checksum_valid(isin_value) else (0.3 if isin_value else 0.0)

    currency_value = normalize_currency(raw.get("currency"))
    amount_value = normalize_amount(raw.get("aggregate_nominal_amount"))
    coupon_value = normalize_amount(raw.get("coupon_rate"))
    maturity_value = normalize_date(raw.get("maturity_date"))
    issue_value = normalize_date(raw.get("issue_date"))

    return ProspectusFields(
        isin=field(isin_value, isin_confidence),
        issuer_name=field(raw.get("issuer_name"), 0.7 if raw.get("issuer_name") else 0.0),
        currency=field(currency_value, 0.8 if currency_value else 0.0),
        aggregate_nominal_amount=field(amount_value, 0.8 if amount_value is not None else 0.0),
        coupon_rate=field(coupon_value, 0.6 if coupon_value is not None else 0.0),
        maturity_date=field(maturity_value, 0.8 if maturity_value else 0.0),
        issue_date=field(issue_value, 0.8 if issue_value else 0.0),
        governing_law=field(raw.get("governing_law"), 0.7 if raw.get("governing_law") else 0.0),
        listing=field(raw.get("listing"), 0.6 if raw.get("listing") else 0.0),
        document_type=field(raw.get("document_type"), 0.9 if raw.get("document_type") else 0.0),
    )
