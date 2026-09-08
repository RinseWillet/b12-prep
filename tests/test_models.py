from my_package.models.prospectus import ExtractedField, ProspectusFields


def test_extracted_field_defaults_are_sentinel():
    field = ExtractedField[str]()
    assert field.value is None
    assert field.confidence == 0.0
    assert field.extraction_method == "stub"


def test_prospectus_fields_accepts_all_sentinel_defaults():
    fields = ProspectusFields()
    assert fields.isin.value is None
    assert fields.document_type.value is None


def test_isin_validator_downgrades_confidence_for_bad_format():
    fields = ProspectusFields(isin=ExtractedField[str](value="not-an-isin", confidence=0.9))
    assert fields.isin.confidence <= 0.2


def test_isin_validator_keeps_confidence_for_valid_format():
    fields = ProspectusFields(isin=ExtractedField[str](value="XS0876756452", confidence=0.9))
    assert fields.isin.confidence == 0.9


def test_currency_validator_downgrades_confidence_for_bad_format():
    fields = ProspectusFields(currency=ExtractedField[str](value="dollars", confidence=0.9))
    assert fields.currency.confidence <= 0.2


def test_common_code_validator_downgrades_confidence_for_bad_format():
    fields = ProspectusFields(common_code=ExtractedField[str](value="12345", confidence=0.9))
    assert fields.common_code.confidence <= 0.2


def test_common_code_validator_keeps_confidence_for_valid_format():
    fields = ProspectusFields(common_code=ExtractedField[str](value="123456789", confidence=0.9))
    assert fields.common_code.confidence == 0.9


def test_lei_validator_downgrades_confidence_for_bad_format():
    fields = ProspectusFields(issuer_lei=ExtractedField[str](value="NOT-A-LEI", confidence=0.9))
    assert fields.issuer_lei.confidence <= 0.2


def test_coupon_type_validator_downgrades_confidence_for_unknown_value():
    fields = ProspectusFields(coupon_type=ExtractedField[str](value="variable", confidence=0.9))
    assert fields.coupon_type.confidence <= 0.2


def test_coupon_type_validator_keeps_confidence_for_known_value():
    fields = ProspectusFields(coupon_type=ExtractedField[str](value="fixed", confidence=0.9))
    assert fields.coupon_type.confidence == 0.9


def test_issue_price_validator_downgrades_confidence_for_implausible_value():
    fields = ProspectusFields(issue_price=ExtractedField[float](value=500.0, confidence=0.9))
    assert fields.issue_price.confidence <= 0.2
