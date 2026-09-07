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
