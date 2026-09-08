"""Prefect 2.2 flow orchestrating PDF discovery, extraction, post-processing, and output."""
import json
from pathlib import Path
from typing import Any, Dict, List

from prefect import flow, get_run_logger, task

from my_package.extraction.llm_client import OllamaExtractor, get_llm_extractor
from my_package.extraction.pdf_reader import extract_text_from_pdf, join_pages
from my_package.postprocessing.rules import postprocess


@task
def discover_pdfs(source_dir: str) -> List[Path]:
    return sorted(Path(source_dir).rglob("*.pdf"))


@task(retries=2, retry_delay_seconds=5)
def extract_pdf_text(path: Path) -> str:
    pages = extract_text_from_pdf(path)
    return join_pages(pages)


@task
def run_extraction(text: str, path: Path) -> Dict[str, Any]:
    extractor = get_llm_extractor()
    raw = extractor.extract(text)
    method = "llm" if isinstance(extractor, OllamaExtractor) else "stub"
    fields = postprocess(raw, method=method, source_text=text)
    return {"filename": path.name, "issuer": path.parent.name, "fields": fields.dict()}


@task
def write_result(result: Dict[str, Any], output_dir: str) -> Path:
    out_path = Path(output_dir) / f"{Path(result['filename']).stem}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, default=str))
    return out_path


@flow(name="prospectus-extraction")
def prospectus_extraction_flow(source_dir: str, output_dir: str) -> List[Path]:
    logger = get_run_logger()
    # Discover all PDF files in the source directory.
    pdf_paths = discover_pdfs(source_dir)
    logger.info(f"Discovered {len(pdf_paths)} PDFs under {source_dir}")

    # Extract text from each PDF and run the extraction pipeline.
    output_paths: List[Path] = []
    failures: List[str] = []
    for path in pdf_paths:
        # Isolate each document so one PDF's failure (e.g. an LLM timeout) doesn't abort the batch.
        try:
            text = extract_pdf_text(path)
            result = run_extraction(text, path)
            output_paths.append(write_result(result, output_dir))
        except Exception as exc:
            failures.append(path.name)
            logger.warning(f"Extraction failed for {path.name}: {exc}")
    logger.info(f"Completed {len(output_paths)}/{len(pdf_paths)} PDFs; {len(failures)} failed")
    return output_paths
