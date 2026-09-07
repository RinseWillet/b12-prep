from pathlib import Path

from my_package.extraction.pdf_reader import extract_text_from_pdf, join_pages

SAMPLE_PDF = (
    Path(__file__).resolve().parent.parent
    / "prospect documents"
    / "barclays"
    / "XS0876756452__final-terms__6b7fde4dae.pdf"
)


def test_extract_text_from_pdf_returns_non_empty_pages():
    pages = extract_text_from_pdf(SAMPLE_PDF)
    assert len(pages) > 0
    assert any(page.text.strip() for page in pages)


def test_page_numbers_are_sequential_starting_at_one():
    pages = extract_text_from_pdf(SAMPLE_PDF)
    assert [p.page_number for p in pages] == list(range(1, len(pages) + 1))


def test_join_pages_concatenates_all_page_text():
    pages = extract_text_from_pdf(SAMPLE_PDF)
    joined = join_pages(pages)
    assert isinstance(joined, str)
    assert "Final Terms" in joined
