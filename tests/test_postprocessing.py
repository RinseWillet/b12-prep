from datetime import date

from my_package.postprocessing.rules import (
    isin_checksum_valid,
    normalize_amount,
    normalize_coupon_type,
    normalize_currency,
    normalize_date,
    normalize_frequency,
    postprocess,
)


def test_isin_checksum_valid_for_known_good_isin():
    assert isin_checksum_valid("XS0876756452") is True


def test_isin_checksum_invalid_for_bad_check_digit():
    assert isin_checksum_valid("XS0876756450") is False


def test_isin_checksum_invalid_for_malformed_input():
    assert isin_checksum_valid("not-an-isin") is False
    assert isin_checksum_valid(None) is False


def test_normalize_date_handles_common_formats():
    assert normalize_date("18 January 2038") == date(2038, 1, 18)
    assert normalize_date("2038-01-18") == date(2038, 1, 18)
    assert normalize_date(None) is None


def test_normalize_currency_maps_symbol_and_code():
    assert normalize_currency("$") == "USD"
    assert normalize_currency("gbp") == "GBP"
    assert normalize_currency("not-a-currency") is None


def test_normalize_currency_maps_rmb_alias():
    assert normalize_currency("RMB") == "CNY"
    assert normalize_currency("Renminbi") == "CNY"
    assert normalize_currency("\u5143") == "CNY"


def test_normalize_amount_strips_separators():
    assert normalize_amount("750,000,000") == 750000000.0
    assert normalize_amount(None) is None


def test_normalize_coupon_type_maps_known_phrases():
    assert normalize_coupon_type("Fixed Rate") == "fixed"
    assert normalize_coupon_type("floating rate") == "floating"
    assert normalize_coupon_type("Zero Coupon") == "zero"
    assert normalize_coupon_type("variable") is None


def test_normalize_frequency_maps_known_phrases():
    assert normalize_frequency("annually") == "annual"
    assert normalize_frequency("Semi-Annually") == "semi-annual"
    assert normalize_frequency("never") is None


def test_postprocess_produces_valid_prospectus_fields():
    raw = {
        "isin": "XS0876756452",
        "issuer_name": "Standard Chartered PLC",
        "currency": "GBP",
        "aggregate_nominal_amount": "750,000,000",
        "coupon_rate": "4.375",
        "maturity_date": "18 January 2038",
        "issue_date": "17 January 2013",
        "governing_law": None,
        "listing": "Official List of the UK Listing Authority",
        "document_type": "Final Terms",
    }
    fields = postprocess(raw)
    assert fields.isin.value == "XS0876756452"
    assert fields.isin.confidence > 0.5
    assert fields.maturity_date.value == date(2038, 1, 18)
    assert fields.governing_law.value is None
    assert fields.governing_law.confidence == 0.0


def test_postprocess_normalizes_new_reference_data_fields():
    raw = {
        "common_code": "123456789",
        "issuer_lei": "U4LOSYZ7YG4W3S5F2G91",
        "coupon_type": "Fixed Rate",
        "interest_payment_frequency": "annually",
        "issue_price": "99.75",
        "seniority": "Senior",
    }
    fields = postprocess(raw)
    assert fields.common_code.value == "123456789"
    assert fields.common_code.confidence > 0.5
    assert fields.coupon_type.value == "fixed"
    assert fields.interest_payment_frequency.value == "annual"
    assert fields.issue_price.value == 99.75
    assert fields.seniority.value == "Senior"


def test_postprocess_grounding_drops_identifiers_absent_from_source():
    raw = {
        "isin": "XS0876756452",
        "issuer_lei": "U4LOSYZ7YG4W3S5F2G91",
        "common_code": "123456789",
    }
    source = "ISIN Code: XS0876756452 and Common Code 123456789 for this security."
    fields = postprocess(raw, source_text=source)
    # ISIN and common code appear in the source; LEI does not -> dropped as hallucinated.
    assert fields.isin.value == "XS0876756452"
    assert fields.common_code.value == "123456789"
    assert fields.issuer_lei.value is None
    assert fields.issuer_lei.confidence == 0.0


def test_postprocess_without_source_text_keeps_identifiers():
    raw = {"issuer_lei": "U4LOSYZ7YG4W3S5F2G91"}
    fields = postprocess(raw)
    assert fields.issuer_lei.value == "U4LOSYZ7YG4W3S5F2G91"

