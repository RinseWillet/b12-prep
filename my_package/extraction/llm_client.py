"""LLM extraction interface: a local Ollama client and a deterministic stub fallback."""
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load OLLAMA_* (and other) settings from a local, gitignored .env file if present.
load_dotenv()

# Deterministic field patterns, tuned against real ICMA-style Final Terms wording.
FIELD_PATTERNS: Dict[str, str] = {
    "isin": r"ISIN(?:\s*Code)?[:\s]+([A-Z]{2}[A-Z0-9]{9}[0-9])",
    "issuer_name": r"\bIssuer:\s*([^\n]+)",
    "currency": r"Currency(?: or Currencies)?:\s*([A-Z]{3})",
    "aggregate_nominal_amount": r"Aggregate Nominal Amount:?[\s\S]{0,100}?[£$€]\s?([\d,]+(?:\.\d+)?)",
    "coupon_rate": r"(?:Rate of Interest|Interest Rate)[:\s]+([\d.]+)\s*(?:per cent\.?|%)",
    "maturity_date": r"Maturity Date:\s*(\d{1,2}\s+\w+\s+\d{4})",
    "issue_date": r"Issue Date:\s*(\d{1,2}\s+\w+\s+\d{4})",
    "governing_law": r"Governing Law[:\s]+([^\n]+)",
    "listing": r"\(i\)\s*Listing:\s*([^\n]+)",
    "document_type": r"(Final Terms|Pricing Supplement)",
    "common_code": r"Common Code[:\s]+(\d{9})",
    "clearing_systems": r"Clearing System[^\n:]*:\s*([^\n]+)",
    "specified_denomination": r"Specified Denomination[s]?[^\n:]*:\s*([^\n]+)",
    "form_of_notes": r"Form of the Notes[^\n:]*:\s*([^\n]+)",
    "coupon_type": r"(Fixed Rate|Floating Rate|Zero Coupon)\s+Note",
    "interest_payment_frequency": r"(semi-annually|annually|quarterly|monthly)",
    "issue_price": r"Issue Price[:\s]+([\d.]+)\s*(?:per cent\.?|%)",
    "seniority": r"Status of the Notes[^\n:]*:\s*([^\n]+)",
    "issuer_lei": r"Legal Entity Identifier(?:\s*\(LEI\))?[:\s]+([A-Z0-9]{20})",
    "guarantor_name": r"\bGuarantor:\s*([^\n]+)",
}

_ISIN_BODY = r"[A-Z]{2}[A-Z0-9]{9}[0-9]"
ISIN_CODE_PATTERN = re.compile(r"ISIN\s*Code[:\s]+(" + _ISIN_BODY + r")", re.IGNORECASE)
ISIN_GENERIC_PATTERN = re.compile(r"ISIN[:\s]+(" + _ISIN_BODY + r")", re.IGNORECASE)


# Prefer the issue's own labelled "ISIN Code"; underlying/reference ISINs often appear
# as "(ISIN: DE...)" earlier, so take the last match to favour the operational section.
def extract_isin(text: str) -> Optional[str]:
    code_matches = ISIN_CODE_PATTERN.findall(text)
    if code_matches:
        return code_matches[-1].upper()
    generic_matches = ISIN_GENERIC_PATTERN.findall(text)
    return generic_matches[-1].upper() if generic_matches else None


# The strongly-labelled "ISIN Code" match only, used to deterministically override an
# LLM that may otherwise return an underlying/reference ISIN.
def extract_labelled_isin(text: str) -> Optional[str]:
    code_matches = ISIN_CODE_PATTERN.findall(text)
    return code_matches[-1].upper() if code_matches else None


# Split text into overlapping windows so no field is lost across a boundary. Capped so a
# very long document (e.g. a whole book) stays bounded instead of firing hundreds of calls.
def chunk_text(text: str, size: int, overlap: int, max_chunks: int) -> List[str]:
    if not text:
        return []
    if len(text) <= size:
        return [text]
    chunks: List[str] = []
    step = max(1, size - overlap)
    start = 0
    while start < len(text) and len(chunks) < max_chunks:
        chunks.append(text[start:start + size])
        start += step
    return chunks


class LLMExtractor(ABC):
    @abstractmethod
    def extract(self, text: str) -> Dict[str, Any]:
        raise NotImplementedError


class StubLLMExtractor(LLMExtractor):
    """Deterministic regex-based stand-in for a real LLM call; explainable, offline, free."""

    def extract(self, text: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for field_name, pattern in FIELD_PATTERNS.items():
            if field_name == "isin":
                result[field_name] = extract_isin(text)
                continue
            match = re.search(pattern, text, re.IGNORECASE)
            result[field_name] = match.group(1).strip() if match else None
        return result


class OllamaExtractor(LLMExtractor):
    """Real LLM extractor calling a local Ollama server via its OpenAI-compatible endpoint.

    GitHub Models (the original free API this used) was fully retired on 2026-07-30,
    so local inference via Ollama replaces it as the free "real LLM" option.
    """

    ENDPOINT = "http://localhost:11434/v1"
    MODEL = "llama3.2:3b"
    PROMPT_VARIANT = "v1"
    REQUEST_TIMEOUT = 180.0
    CHUNK_CHARS = 12000
    CHUNK_OVERLAP = 500
    MAX_CHUNKS = 6

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        prompt_variant: Optional[str] = None,
    ) -> None:
        from openai import OpenAI

        self._base_url = base_url or os.environ.get("OLLAMA_ENDPOINT", self.ENDPOINT)
        self._model = model or os.environ.get("OLLAMA_MODEL", self.MODEL)
        self._prompt_variant = prompt_variant or os.environ.get(
            "OLLAMA_PROMPT_VARIANT", self.PROMPT_VARIANT
        )
        # Bounded timeout + no retries so a stuck document fails fast instead of hanging the batch.
        self._client = OpenAI(
            base_url=self._base_url,
            api_key="ollama",
            timeout=self.REQUEST_TIMEOUT,
            max_retries=0,
        )

    def extract(self, text: str) -> Dict[str, Any]:
        merged: Dict[str, Any] = {name: None for name in FIELD_PATTERNS}
        for chunk in chunk_text(text, self.CHUNK_CHARS, self.CHUNK_OVERLAP, self.MAX_CHUNKS):
            raw = self._extract_chunk(chunk)
            for key in FIELD_PATTERNS:
                if merged[key] is None and raw.get(key) is not None:
                    merged[key] = raw.get(key)
        # Hybrid override: a strongly-labelled "ISIN Code" is authoritative over the LLM.
        labelled_isin = extract_labelled_isin(text)
        if labelled_isin:
            merged["isin"] = labelled_isin
        return merged

    def _extract_chunk(self, chunk: str) -> Dict[str, Any]:
        prompt = self._build_prompt(chunk)
        system_prompt = self._system_prompt()
        # Qwen3 emits <think> reasoning by default, which corrupts strict JSON output;
        # /no_think switches it off via Ollama's chat template.
        if "qwen3" in self._model.lower():
            system_prompt += "\n/no_think"
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        return self._parse_response(response)

    _SYSTEM_PROMPT = (
        "You extract structured reference data from Eurobond Final Terms / Pricing "
        "Supplements. Return only a flat JSON object. Follow these rules strictly:\n"
        "- isin: the ISIN of THIS security (labelled 'ISIN Code'). Never return the "
        "ISIN of an underlying, reference or related instrument.\n"
        "- document_type: exactly 'Final Terms' or 'Pricing Supplement'.\n"
        "- coupon_type: exactly 'fixed', 'floating' or 'zero'.\n"
        "- aggregate_nominal_amount, coupon_rate, issue_price: plain numbers only, "
        "no thousands separators, currency symbols or '%'.\n"
        "- issuer_lei: the 20-character LEI of the issuer.\n"
        "- Use null for any field that is not present. Do not guess."
    )

    # v2 adds per-field hints for the fields that miss most, plus one compact worked
    # example; benchmark it against v1 before making it the default.
    _SYSTEM_PROMPT_V2 = (
        "You extract structured reference data from Eurobond Final Terms / Pricing "
        "Supplements. Return only a flat JSON object, no commentary. Follow these rules "
        "strictly:\n"
        "- isin: the ISIN of THIS security (labelled 'ISIN Code'). Never return the "
        "ISIN of an underlying, reference or related instrument.\n"
        "- document_type: exactly 'Final Terms' or 'Pricing Supplement'.\n"
        "- coupon_type: exactly 'fixed', 'floating' or 'zero' (a 'Fixed Rate Note' is "
        "'fixed'; a 'Zero Coupon Note' is 'zero').\n"
        "- interest_payment_frequency: one of 'annual', 'semi-annual', 'quarterly', "
        "'monthly'. Map 'payable annually' -> 'annual', 'per annum' -> 'annual', 'semi-annually' -> 'semi-annual'.\n"
        "- seniority: 'Senior' or 'Subordinated', taken from the 'Status of the Notes'.\n"
        "- common_code: the 9-digit Common Code only, digits with no spaces.\n"
        "- aggregate_nominal_amount, coupon_rate, issue_price: plain numbers only, no "
        "thousands separators, currency symbols or '%' (e.g. '99.653 per cent.' -> "
        "99.653; 'GBP 750,000,000' -> 750000000).\n"
        "- currency: the 3-letter ISO code (e.g. 'EUR').\n"
        "- maturity_date, issue_date: ISO format YYYY-MM-DD.\n"
        "- issuer_lei: the 20-character LEI of the issuer.\n"
        "- Use null for any field that is not present. Do not guess.\n"
        "Example (illustrative, values abbreviated):\n"
        "Input: '... ISIN Code: XS1234567890 ... Issuer: Example Bank plc ... 4.5 per "
        "cent. ... interest payable semi-annually ... Status of the Notes: Senior ...'\n"
        'Output: {"isin": "XS1234567890", "issuer_name": "Example Bank plc", '
        '"coupon_rate": 4.5, "coupon_type": "fixed", "interest_payment_frequency": '
        '"semi-annual", "seniority": "Senior"}'
    )

    def _system_prompt(self) -> str:
        if self._prompt_variant == "v2":
            return self._SYSTEM_PROMPT_V2
        return self._SYSTEM_PROMPT

    def _build_prompt(self, text: str) -> str:
        fields = ", ".join(FIELD_PATTERNS.keys())
        return (
            "Extract these fields as a flat JSON object with keys: "
            f"{fields}. Return JSON only, no commentary.\n\n" + text
        )

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        content = response.choices[0].message.content
        if content:
            # Strip any <think>...</think> block a reasoning model may still emit.
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            logger.warning("OllamaExtractor: could not parse model response as JSON")
            return {field_name: None for field_name in FIELD_PATTERNS}


def _ollama_server_reachable(base_url: str, timeout: float = 2.0) -> bool:
    import urllib.request

    tags_url = base_url.rsplit("/v1", 1)[0] + "/api/tags"
    try:
        with urllib.request.urlopen(tags_url, timeout=timeout):
            return True
    except OSError:
        return False


def get_llm_extractor() -> LLMExtractor:
    """Select OllamaExtractor when a local Ollama server is reachable, else fall back to the stub."""
    base_url = os.environ.get("OLLAMA_ENDPOINT", OllamaExtractor.ENDPOINT)
    if not _ollama_server_reachable(base_url):
        logger.warning("Ollama server not reachable at %s; using StubLLMExtractor", base_url)
        return StubLLMExtractor()
    return OllamaExtractor(base_url=base_url)
