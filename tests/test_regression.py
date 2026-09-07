"""Regression test comparing extraction output to a small hand-curated ground truth.

Ground truth values below were read directly from the source PDF text (not from the
filename) to keep ISIN/field extraction independent of filename metadata.
"""
from datetime import date
from pathlib import Path

from my_package.extraction.llm_client import StubLLMExtractor
from my_package.extraction.pdf_reader import extract_text_from_pdf, join_pages
from my_package.postprocessing.rules import postprocess

PROSPECT_DIR = Path(__file__).resolve().parent.parent / "prospect documents"

GROUND_TRUTH = {
    PROSPECT_DIR / "barclays" / "XS0876756452__final-terms__6b7fde4dae.pdf": {
        "isin": "XS0876756452",
        "issuer_name": "Standard Chartered PLC",
        "currency": "GBP",
        "maturity_date": date(2038, 1, 18),
        "document_type": "Final Terms",
    },
}


def _extract(path: Path):
    text = join_pages(extract_text_from_pdf(path))
    raw = StubLLMExtractor().extract(text)
    return postprocess(raw)


def test_extraction_matches_ground_truth_for_sample_documents():
    for path, expected in GROUND_TRUTH.items():
        fields = _extract(path)
        assert fields.isin.value == expected["isin"]
        assert fields.issuer_name.value == expected["issuer_name"]
        assert fields.currency.value == expected["currency"]
        assert fields.maturity_date.value == expected["maturity_date"]
        assert fields.document_type.value == expected["document_type"]


def test_extraction_degrades_gracefully_on_text_free_pdf():
    # hsbc/XS0159497162.pdf has no extractable text layer (scanned image) - fields
    # must fall back to sentinel None rather than raise or fabricate values.
    scanned_pdf = PROSPECT_DIR / "hsbc" / "XS0159497162.pdf"
    fields = _extract(scanned_pdf)
    assert fields.isin.value is None
    assert fields.isin.confidence == 0.0
