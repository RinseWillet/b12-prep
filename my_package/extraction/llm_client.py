"""LLM extraction interface: a local Ollama client and a deterministic stub fallback."""
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

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
}


class LLMExtractor(ABC):
    @abstractmethod
    def extract(self, text: str) -> Dict[str, Any]:
        raise NotImplementedError


class StubLLMExtractor(LLMExtractor):
    """Deterministic regex-based stand-in for a real LLM call; explainable, offline, free."""

    def extract(self, text: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for field_name, pattern in FIELD_PATTERNS.items():
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
    MAX_CHARS = 12000

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None) -> None:
        from openai import OpenAI

        self._base_url = base_url or os.environ.get("OLLAMA_ENDPOINT", self.ENDPOINT)
        self._model = model or os.environ.get("OLLAMA_MODEL", self.MODEL)
        self._client = OpenAI(base_url=self._base_url, api_key="ollama")

    def extract(self, text: str) -> Dict[str, Any]:
        prompt = self._build_prompt(text)
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return self._parse_response(response)

    def _build_prompt(self, text: str) -> str:
        fields = ", ".join(FIELD_PATTERNS.keys())
        return (
            "Extract the following fields from this Eurobond prospectus excerpt as a "
            f"flat JSON object with keys: {fields}. Use null for any field not present. "
            "Return JSON only, no commentary.\n\n" + text[: self.MAX_CHARS]
        )

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        content = response.choices[0].message.content
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
