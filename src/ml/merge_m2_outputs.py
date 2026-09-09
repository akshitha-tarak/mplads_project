"""Merge cost-anomaly and duplicate-detection outputs for M2."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DUPLICATE = PROJECT_ROOT / "data" / "processed" / "duplicate_outputs.csv"
DEFAULT_ANOMALY = (
    PROJECT_ROOT / "data" / "processed" / "cost_anomaly_outputs.csv"
)
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "m2_ml_outputs.csv"

def _normalize_anomaly_columns(anomaly: pd.DataFrame) -> pd.DataFrame:
    """Normalize current and legacy anomaly result column names."""
    aliases = {
        "cost_anomaly_flag": "cost_anomaly_flag",
        "cost_anomaly_score": "cost_anomaly_score",
        "anomaly_score": "cost_anomaly_score",
        "cost_anomaly_reason": "cost_anomaly_reason",
        "anomaly_reason": "cost_anomaly_reason",
    }
    required = {"cost_anomaly_flag", "cost_anomaly_score", "cost_anomaly_reason"}
    if "cost_anomaly_flag" not in anomaly.columns:
        raise ValueError("Anomaly output missing columns: ['cost_anomaly_flag']")
    available = {source: target for source, target in aliases.items() if source in anomaly.columns}
    missing = required.difference(set(available.values()))
    if missing:
        raise ValueError(f"Anomaly output missing columns: {sorted(missing)}")
    columns = ["project_id", *available]
    if "cost_anomaly_available" in anomaly.columns:
        columns.append("cost_anomaly_available")
    return anomaly[columns].rename(columns=available)


def _read_unique(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{label} output not found: {path}")
    frame = pd.read_csv(path)
    if "project_id" not in frame.columns:
        raise ValueError(f"{label} output must contain project_id: {path}")
    if frame["project_id"].duplicated().any():
        raise ValueError(f"{label} output must contain one row per project_id: {path}")
    return frame


def merge_m2_outputs(
    duplicate_path: str | Path = DEFAULT_DUPLICATE,
    anomaly_path: str | Path = DEFAULT_ANOMALY,
    output_path: str | Path = DEFAULT_OUTPUT,
) -> pd.DataFrame:
    """Merge duplicate results with normalized cost-anomaly results.

    Projects absent from the anomaly file retain a null anomaly flag and have
    cost_anomaly_available=False; absence is not treated as a normal project.
    """
    duplicate = _read_unique(Path(duplicate_path), "Duplicate")
    anomaly = _read_unique(Path(anomaly_path), "Anomaly")

    anomaly = _normalize_anomaly_columns(anomaly)
    if "cost_anomaly_available" not in anomaly.columns:
        anomaly["cost_anomaly_available"] = True

    merged = duplicate.merge(anomaly, on="project_id", how="left", validate="one_to_one")
    merged["cost_anomaly_available"] = merged["cost_anomaly_available"].fillna(False).astype(bool)
    merged["cost_anomaly_reason"] = merged["cost_anomaly_reason"].fillna("")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)

    analyzed = int(merged["cost_anomaly_available"].sum())
    print(f"Projects merged: {len(merged)}")
    print(f"Anomaly coverage: {analyzed}/{len(merged)}")
    print(f"Output: {output_path}")
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duplicates", type=Path, default=DEFAULT_DUPLICATE)
    parser.add_argument("--anomalies", type=Path, default=DEFAULT_ANOMALY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    merge_m2_outputs(args.duplicates, args.anomalies, args.output)


if __name__ == "__main__":
    main()
