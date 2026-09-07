from datetime import date

from my_package.postprocessing.rules import (
    isin_checksum_valid,
    normalize_amount,
    normalize_currency,
    normalize_date,
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


def test_normalize_amount_strips_separators():
    assert normalize_amount("750,000,000") == 750000000.0
    assert normalize_amount(None) is None


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
