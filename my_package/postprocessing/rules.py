"""Deterministic post-processing: normalization, ISIN validation, and sentinel/confidence rules."""
import re
from datetime import date, datetime
from typing import Any, Dict, Optional

from my_package.models.prospectus import ExtractedField, ProspectusFields

ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")
COMMON_CODE_PATTERN = re.compile(r"^\d{9}$")
LEI_PATTERN = re.compile(r"^[A-Z0-9]{20}$")
_LETTER_VALUES = {chr(ord("A") + i): str(10 + i) for i in range(26)}
DATE_FORMATS = ["%d %B %Y", "%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"]
CURRENCY_SYMBOLS = {"$": "USD", "\u20ac": "EUR", "\u00a3": "GBP", "\u00a5": "JPY", "\u5143": "CNY"}
# Textual currency aliases that are not valid ISO 4217 codes (e.g. "RMB" -> "CNY").
CURRENCY_ALIASES = {"RMB": "CNY", "RENMINBI": "CNY"}
COUPON_TYPE_MAP = {"fixed rate": "fixed", "floating rate": "floating", "zero coupon": "zero"}
FREQUENCY_MAP = {
    "annually": "annual",
    "semi-annually": "semi-annual",
    "quarterly": "quarterly",
    "monthly": "monthly",
}


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
    if upper in CURRENCY_ALIASES:
        return CURRENCY_ALIASES[upper]
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

# Normalize a coupon type phrase into one of: fixed, floating, zero. Returns None if unknown.
def normalize_coupon_type(raw: Optional[Any]) -> Optional[str]:
    if not raw or not isinstance(raw, str):
        return None
    return COUPON_TYPE_MAP.get(raw.strip().lower())

# Normalize an interest payment frequency phrase into a canonical adverb. Returns None if unknown.
def normalize_frequency(raw: Optional[Any]) -> Optional[str]:
    if not raw or not isinstance(raw, str):
        return None
    return FREQUENCY_MAP.get(raw.strip().lower())

# Coerce an arbitrary LLM value into a string (LLMs may return lists/numbers for text fields).
def _as_text(raw: Optional[Any]) -> Optional[str]:
    if raw is None:
        return None
    if isinstance(raw, str):
        return raw
    if isinstance(raw, (list, tuple)):
        return ", ".join(str(x) for x in raw)
    return str(raw)


# Anti-hallucination guard: an identifier the model returns must appear verbatim in the
# source. With no source_text we cannot check, so the value is left untouched.
def _grounded(token: Optional[Any], source_text: Optional[str]) -> bool:
    if not token or not source_text:
        return True
    return str(token).strip().upper() in source_text.upper()

# Postprocess a raw extraction dictionary into a ProspectusFields object, normalizing and validating fields.
def postprocess(raw: Dict[str, Any], method: str = "stub", source_text: Optional[str] = None) -> ProspectusFields:
    """Normalize, validate, and attach confidence/sentinel metadata to a raw extraction dict.

    When source_text is given, identifier fields (isin, issuer_lei, common_code) that do
    not appear verbatim in the source are dropped as hallucinations.
    """

    def field(value: Any, confidence: float) -> ExtractedField:
        return ExtractedField(value=value, confidence=confidence, extraction_method=method)

    isin_value = raw.get("isin")
    if not _grounded(isin_value, source_text):
        isin_value = None
    isin_confidence = 0.9 if isin_checksum_valid(isin_value) else (0.3 if isin_value else 0.0)

    currency_value = normalize_currency(raw.get("currency"))
    amount_value = normalize_amount(raw.get("aggregate_nominal_amount"))
    coupon_value = normalize_amount(raw.get("coupon_rate"))
    maturity_value = normalize_date(raw.get("maturity_date"))
    issue_value = normalize_date(raw.get("issue_date"))

    common_code_value = raw.get("common_code")
    if not _grounded(common_code_value, source_text):
        common_code_value = None
    common_code_confidence = (
        0.9 if common_code_value and COMMON_CODE_PATTERN.match(str(common_code_value))
        else (0.3 if common_code_value else 0.0)
    )
    lei_value = raw.get("issuer_lei")
    if not _grounded(lei_value, source_text):
        lei_value = None
    lei_confidence = (
        0.9 if lei_value and LEI_PATTERN.match(str(lei_value))
        else (0.3 if lei_value else 0.0)
    )
    coupon_type_value = normalize_coupon_type(raw.get("coupon_type"))
    frequency_value = normalize_frequency(raw.get("interest_payment_frequency"))
    issue_price_value = normalize_amount(raw.get("issue_price"))

    return ProspectusFields(
        isin=field(isin_value, isin_confidence),
        issuer_name=field(_as_text(raw.get("issuer_name")), 0.7 if raw.get("issuer_name") else 0.0),
        currency=field(currency_value, 0.8 if currency_value else 0.0),
        aggregate_nominal_amount=field(amount_value, 0.8 if amount_value is not None else 0.0),
        coupon_rate=field(coupon_value, 0.6 if coupon_value is not None else 0.0),
        maturity_date=field(maturity_value, 0.8 if maturity_value else 0.0),
        issue_date=field(issue_value, 0.8 if issue_value else 0.0),
        governing_law=field(_as_text(raw.get("governing_law")), 0.7 if raw.get("governing_law") else 0.0),
        listing=field(_as_text(raw.get("listing")), 0.6 if raw.get("listing") else 0.0),
        document_type=field(_as_text(raw.get("document_type")), 0.9 if raw.get("document_type") else 0.0),
        common_code=field(_as_text(common_code_value), common_code_confidence),
        clearing_systems=field(_as_text(raw.get("clearing_systems")), 0.6 if raw.get("clearing_systems") else 0.0),
        specified_denomination=field(
            _as_text(raw.get("specified_denomination")), 0.6 if raw.get("specified_denomination") else 0.0
        ),
        form_of_notes=field(_as_text(raw.get("form_of_notes")), 0.6 if raw.get("form_of_notes") else 0.0),
        coupon_type=field(coupon_type_value, 0.8 if coupon_type_value else 0.0),
        interest_payment_frequency=field(frequency_value, 0.7 if frequency_value else 0.0),
        issue_price=field(issue_price_value, 0.8 if issue_price_value is not None else 0.0),
        seniority=field(_as_text(raw.get("seniority")), 0.6 if raw.get("seniority") else 0.0),
        issuer_lei=field(_as_text(lei_value), lei_confidence),
        guarantor_name=field(_as_text(raw.get("guarantor_name")), 0.7 if raw.get("guarantor_name") else 0.0),
    )
