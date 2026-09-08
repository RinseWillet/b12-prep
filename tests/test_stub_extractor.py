from my_package.extraction.llm_client import (
    StubLLMExtractor,
    chunk_text,
    extract_isin,
    extract_labelled_isin,
)



SAMPLE_TEXT = """
1 Issuer: Standard Chartered PLC
3 Currency or Currencies: GBP
4 Aggregate Nominal Amount:
(i) Series: £750,000,000
9 Maturity Date: 18 January 2038
(i) Issue Date: 17 January 2013
(i) ISIN Code: XS0876756452
Common Code: 123456789
(i) Clearing System: Euroclear and Clearstream
Specified Denomination: £100,000
Status of the Notes: Senior
Guarantor: Standard Chartered Bank
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


def test_stub_extractor_finds_new_reference_data_fields():
    result = StubLLMExtractor().extract(SAMPLE_TEXT)
    assert result["common_code"] == "123456789"
    assert result["clearing_systems"] == "Euroclear and Clearstream"
    assert result["seniority"] == "Senior"
    assert result["guarantor_name"] == "Standard Chartered Bank"


def test_stub_extractor_returns_none_for_missing_fields():
    result = StubLLMExtractor().extract("No relevant information here.")
    assert result["isin"] is None
    assert result["governing_law"] is None


def test_extract_isin_prefers_labelled_code_over_reference_isin():
    # A reference ISIN of an underlying appears before the issue's own ISIN Code.
    text = "Interest linked to bond (ISIN: DE0001102473)\n8. ISIN Code: XS2904540775"
    assert extract_isin(text) == "XS2904540775"


def test_extract_isin_falls_back_to_generic_label():
    assert extract_isin("ISIN: XS0876756452") == "XS0876756452"
    assert extract_isin("no securities here") is None


def test_extract_labelled_isin_ignores_generic_and_reference_isins():
    # Only a strongly-labelled "ISIN Code" is authoritative for the LLM override.
    assert extract_labelled_isin("ISIN Code: XS2904540775") == "XS2904540775"
    assert extract_labelled_isin("(ISIN: DE0001102473)") is None


def test_chunk_text_returns_single_chunk_when_text_fits():
    assert chunk_text("short text", size=100, overlap=10, max_chunks=6) == ["short text"]
    assert chunk_text("", size=100, overlap=10, max_chunks=6) == []


def test_chunk_text_overlaps_and_caps_long_text():
    text = "abcdefghij" * 5  # 50 chars
    chunks = chunk_text(text, size=20, overlap=5, max_chunks=6)
    assert all(len(c) <= 20 for c in chunks)
    assert chunks[0] == text[:20]
    # step = size - overlap = 15, so the second chunk starts at index 15.
    assert chunks[1] == text[15:35]


def test_chunk_text_respects_max_chunks_cap():
    text = "x" * 10000
    chunks = chunk_text(text, size=100, overlap=0, max_chunks=3)
    assert len(chunks) == 3
