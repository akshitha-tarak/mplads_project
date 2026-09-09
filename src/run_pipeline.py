"""Run the complete MPLADS data, ML, and risk-scoring pipeline."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_stage(*command: str) -> None:
    subprocess.run(
        [sys.executable, *command],
        cwd=PROJECT_ROOT,
        check=True,
    )


def run_pipeline(skip_clean: bool = False) -> None:
    if not skip_clean:
        run_stage("src/cleaning/clean_data.py")

    run_stage("src/integration/expenditure_summary.py")
    run_stage("src/integration/create_master_dataset.py")
    run_stage("src/integration/feature_engineering.py")
    run_stage("-m", "src.ml.run_duplicate_detection")
    run_stage("-m", "src.ml.run_cost_anomaly")
    run_stage("-m", "src.ml.merge_m2_outputs")
    run_stage("src/rules/rule_engine.py")

    print("\nPipeline completed successfully.")
    print("Risk output: data/cleaned/risk_output.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="Reuse existing cleaned CSV files and start at expenditure aggregation.",
    )
    args = parser.parse_args()
    run_pipeline(skip_clean=args.skip_clean)


if __name__ == "__main__":
    main()
