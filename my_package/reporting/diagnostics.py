"""Aggregate per-document extraction results into a single diagnostics table."""
import json
from pathlib import Path

import pandas as pd

from my_package.postprocessing.rules import isin_checksum_valid


def build_diagnostics_report(results_dir: str) -> pd.DataFrame:
    rows = []
    for json_path in sorted(Path(results_dir).glob("*.json")):
        data = json.loads(json_path.read_text())
        fields = data["fields"]
        row = {"issuer": data.get("issuer"), "filename": data.get("filename")}
        for name, extracted in fields.items():
            row[f"{name}_value"] = extracted.get("value")
            row[f"{name}_confidence"] = extracted.get("confidence")
        row["isin_checksum_valid"] = isin_checksum_valid(fields.get("isin", {}).get("value"))
        rows.append(row)
    return pd.DataFrame(rows)


def write_diagnostics_csv(results_dir: str, output_csv: str) -> Path:
    df = build_diagnostics_report(results_dir)
    out_path = Path(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return out_path
