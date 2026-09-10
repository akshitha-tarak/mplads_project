"""Run the live M1 / M2 / M3 pipeline.

M1  python -m src.preprocessing.datapreprocessing
M2  src.ml.run_duplicate_detection, run_cost_anomaly, merge_m2_outputs
M3  python -m src.rules.rule_engine
"""

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


def run_pipeline(skip_ml: bool = False, with_m1: bool = False) -> None:
    master = PROJECT_ROOT / "data" / "cleaned" / "master_projects.csv"
    if with_m1 or not master.exists():
        run_stage("-m", "src.preprocessing.datapreprocessing")

    if not master.exists():
        raise FileNotFoundError(
            "Missing data/cleaned/master_projects.csv. "
            "Run python -m src.preprocessing.datapreprocessing first."
        )

    if not skip_ml:
        run_stage("-m", "src.ml.run_duplicate_detection")
        run_stage("-m", "src.ml.run_cost_anomaly")
        run_stage("-m", "src.ml.merge_m2_outputs")

    run_stage("-m", "src.rules.rule_engine")

    print("\nPipeline completed successfully.")
    print("Risk output: data/cleaned/risk_output.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-ml",
        action="store_true",
        help="Reuse existing data/processed M2 CSVs and only re-run M3.",
    )
    parser.add_argument(
        "--with-m1",
        action="store_true",
        help="Rebuild data/cleaned/master_projects.csv before M2/M3.",
    )
    args = parser.parse_args()
    run_pipeline(skip_ml=args.skip_ml, with_m1=args.with_m1)


if __name__ == "__main__":
    main()
