from my_package.extraction.llm_client import StubLLMExtractor

SAMPLE_TEXT = """
1 Issuer: Standard Chartered PLC
3 Currency or Currencies: GBP
4 Aggregate Nominal Amount:
(i) Series: £750,000,000
9 Maturity Date: 18 January 2038
(i) Issue Date: 17 January 2013
(i) ISIN Code: XS0876756452
(i) Listing: Official List of the UK Listing Authority
Final Terms
"""


def test_stub_extractor_finds_fields_from_real_document_wording():
    result = StubLLMExtractor().extract(SAMPLE_TEXT)
    assert result["isin"] == "XS0876756452"
    assert result["currency"] == "GBP"
    assert result["issuer_name"] == "Standard Chartered PLC"
    assert result["maturity_date"] == "18 January 2038"
    assert result["document_type"] == "Final Terms"


def test_stub_extractor_returns_none_for_missing_fields():
    result = StubLLMExtractor().extract("No relevant information here.")
    assert result["isin"] is None
    assert result["governing_law"] is None
