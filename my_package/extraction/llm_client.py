"""LLM extraction interface: a real GitHub Models client and a deterministic stub fallback."""
import json
import logging
import os
import re
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

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


class GitHubModelsExtractor(LLMExtractor):
    """Real LLM extractor calling GitHub Models' OpenAI-compatible inference endpoint."""

    ENDPOINT = "https://models.inference.ai.azure.com"
    MODEL = "gpt-4o-mini"
    MAX_CHARS = 12000

    def __init__(self, token: Optional[str] = None, model: Optional[str] = None) -> None:
        token = token or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GITHUB_TOKEN is required for GitHubModelsExtractor")
        from openai import OpenAI

        self._client = OpenAI(base_url=self.ENDPOINT, api_key=token)
        self._model = model or self.MODEL

    def extract(self, text: str) -> Dict[str, Any]:
        prompt = self._build_prompt(text)
        response = self._call_with_retry(prompt)
        return self._parse_response(response)

    def _build_prompt(self, text: str) -> str:
        fields = ", ".join(FIELD_PATTERNS.keys())
        return (
            "Extract the following fields from this Eurobond prospectus excerpt as a "
            f"flat JSON object with keys: {fields}. Use null for any field not present. "
            "Return JSON only, no commentary.\n\n" + text[: self.MAX_CHARS]
        )

    def _call_with_retry(self, prompt: str, max_retries: int = 3) -> Any:
        from openai import RateLimitError

        for attempt in range(max_retries):
            try:
                return self._client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
            except RateLimitError:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2**attempt)

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            logger.warning("GitHubModelsExtractor: could not parse model response as JSON")
            return {field_name: None for field_name in FIELD_PATTERNS}


def get_llm_extractor() -> LLMExtractor:
    """Select GitHubModelsExtractor when a token is available, else fall back to the stub."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.warning("GITHUB_TOKEN not set; using StubLLMExtractor")
        return StubLLMExtractor()
    try:
        return GitHubModelsExtractor(token=token)
    except RuntimeError:
        logger.warning("Falling back to StubLLMExtractor: GitHubModelsExtractor unavailable")
        return StubLLMExtractor()
