"""Run the spec-compliant cost anomaly detector on the M1 master."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.ml.cost_anomaly import detect_cost_anomalies, save_model

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "cleaned" / "master_projects.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "cost_anomaly_outputs.csv"
DEFAULT_MODEL = PROJECT_ROOT / "models" / "cost_isolation_forest.joblib"


def run_cost_anomaly(
    input_path: str | Path = DEFAULT_INPUT,
    output_path: str | Path = DEFAULT_OUTPUT,
    model_path: str | Path = DEFAULT_MODEL,
) -> pd.DataFrame:
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Master file not found: {input_path}")
    projects = pd.read_csv(input_path)
    results, model = detect_cost_anomalies(projects)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_path, index=False)
    if model.steps:
        save_model(model, model_path)
    print(f"Projects analysed: {int(results['cost_anomaly_available'].sum())}")
    print(f"Cost anomalies: {int(results['cost_anomaly_flag'].fillna(0).sum())}")
    print(f"Output: {output_path}")
    print(f"Model: {model_path}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args()
    run_cost_anomaly(args.input, args.output, args.model)


if __name__ == "__main__":
    main()
