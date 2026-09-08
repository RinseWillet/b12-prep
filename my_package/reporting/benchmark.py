"""Benchmark extractor accuracy against a hand-curated gold reference.

Scores every available extractor (the regex Stub baseline and, when a local
Ollama server is reachable, the Ollama LLM) against gold values curated from the
source PDFs. Comparison is exact-match; a case-insensitive mode can be layered on
later to quantify near-misses.
"""
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

import pandas as pd
import re

from my_package.extraction.llm_client import (
    LLMExtractor,
    OllamaExtractor,
    StubLLMExtractor,
    _ollama_server_reachable,
)
from my_package.extraction.pdf_reader import extract_text_from_pdf, join_pages
from my_package.postprocessing.rules import postprocess


def _available_extractors(models: Optional[Iterable[str]] = None) -> Dict[str, LLMExtractor]:
    extractors: Dict[str, LLMExtractor] = {"stub": StubLLMExtractor()}
    if _ollama_server_reachable(OllamaExtractor.ENDPOINT):
        if models:
            for model in models:
                extractors["ollama:" + model] = OllamaExtractor(model=model)
        else:
            extractors["ollama"] = OllamaExtractor()
    return extractors


# Reduce a value to a type-normalized form so gold JSON (strings/numbers) and typed
# extractor output (date/float/str) compare cleanly under exact match.
def _to_comparable(value: Any) -> Optional[Any]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    text = str(value).strip()
    try:
        return float(text.replace(",", ""))
    except ValueError:
        return text


# Collapse a string to lowercase alphanumerics for lenient comparison.
def _lenient_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _is_match(expected: Any, actual: Any, mode: str) -> bool:
    exp = _to_comparable(expected)
    act = _to_comparable(actual)
    if exp is None and act is None:
        return True
    if exp is None or act is None:
        return False
    if isinstance(exp, str) and isinstance(act, str) and mode == "lenient":
        exp_l, act_l = _lenient_text(exp), _lenient_text(act)
        return exp_l == act_l or exp_l in act_l or act_l in exp_l
    return exp == act


def _classify(expected: Any, actual: Any, mode: str = "exact") -> str:
    if _is_match(expected, actual, mode):
        return "match"
    if _to_comparable(actual) is None:
        return "missing"
    if _to_comparable(expected) is None:
        return "spurious"
    return "mismatch"


def run_benchmark(gold_path: str, output_csv: str, base_dir: Optional[str] = None, mode: str = "exact", models: Optional[Iterable[str]] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Score each available extractor against the gold fixture; write detail + summary CSVs.

    mode: "exact" for literal comparison, "lenient" for case-insensitive/substring
    matching on text fields (quantifies how near Ollama's misses are).
    models: optional list of Ollama model tags to score side by side (e.g.
    ["llama3.2:3b", "llama3.1:8b"]); each becomes its own "ollama:<model>" column.
    """
    gold_file = Path(gold_path)
    gold: Dict[str, Dict[str, Any]] = json.loads(gold_file.read_text())
    root = Path(base_dir) if base_dir else gold_file.resolve().parent.parent
    extractors = _available_extractors(models)

    rows = []
    for rel_path, expected_fields in gold.items():
        text = join_pages(extract_text_from_pdf(root / rel_path))
        for extractor_name, extractor in extractors.items():
            fields = postprocess(extractor.extract(text), method=extractor_name)
            for field_name, expected in expected_fields.items():
                actual = getattr(fields, field_name).value
                rows.append(
                    {
                        "pdf": rel_path,
                        "field": field_name,
                        "extractor": extractor_name,
                        "expected": expected,
                        "actual": actual,
                        "outcome": _classify(expected, actual, mode),
                    }
                )

    detail = pd.DataFrame(rows)
    summary = _summarize(detail)

    detail_path = Path(output_csv)
    detail_path.parent.mkdir(parents=True, exist_ok=True)
    detail.to_csv(detail_path, index=False)
    summary_path = detail_path.with_name(detail_path.stem + "_summary.csv")
    summary.to_csv(summary_path, index=False)
    return detail, summary


def _summarize(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=["extractor", "matches", "total", "accuracy"])
    grouped = detail.groupby("extractor")
    summary = grouped["outcome"].agg(
        matches=lambda s: (s == "match").sum(),
        total="count",
    ).reset_index()
    summary["accuracy"] = (summary["matches"] / summary["total"]).round(3)
    return summary
