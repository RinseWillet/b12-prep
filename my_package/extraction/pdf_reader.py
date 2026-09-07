"""PDF text extraction utilities."""
from pathlib import Path
from typing import List, NamedTuple

import pdfplumber


class PageText(NamedTuple):
    page_number: int
    text: str


def extract_text_from_pdf(path: Path) -> List[PageText]:
    """Extract per-page text, keeping page numbers for diagnostic source traceability."""
    pages: List[PageText] = []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            pages.append(PageText(page_number=i, text=page.extract_text() or ""))
    return pages


def join_pages(pages: List[PageText]) -> str:
    return "\n".join(p.text for p in pages)
