import os

import pytest

from my_package.extraction.llm_client import GitHubModelsExtractor

SAMPLE_TEXT = """
1 Issuer: Standard Chartered PLC
3 Currency or Currencies: GBP
(i) ISIN Code: XS0876756452
Final Terms
"""


@pytest.mark.skipif(
    not os.environ.get("GITHUB_TOKEN"),
    reason="GITHUB_TOKEN not set; skipping live GitHub Models call",
)
def test_github_models_extractor_returns_json_fields():
    extractor = GitHubModelsExtractor()
    result = extractor.extract(SAMPLE_TEXT)
    assert isinstance(result, dict)
    assert "isin" in result
