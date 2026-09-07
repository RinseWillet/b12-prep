import pytest

from my_package.extraction.llm_client import OllamaExtractor, _ollama_server_reachable

SAMPLE_TEXT = """
1 Issuer: Standard Chartered PLC
3 Currency or Currencies: GBP
(i) ISIN Code: XS0876756452
Final Terms
"""


@pytest.mark.skipif(
    not _ollama_server_reachable(OllamaExtractor.ENDPOINT),
    reason="Local Ollama server not reachable; skipping live extraction call",
)
def test_ollama_extractor_returns_json_fields():
    extractor = OllamaExtractor()
    result = extractor.extract(SAMPLE_TEXT)
    # Small local models don't always populate every key, so just check we got
    # a parsed JSON object back rather than asserting on exact field presence.
    assert isinstance(result, dict)
    assert len(result) > 0
