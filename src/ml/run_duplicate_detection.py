"""Run duplicate detection on the M1 project master dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.ml.duplicate_detection import detect_duplicates, save_vectorizer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "cleaned" / "master_projects.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "duplicate_outputs.csv"
DEFAULT_VECTORIZER = PROJECT_ROOT / "models" / "tfidf_vectorizer.joblib"


def run_duplicate_detection(
    input_path: str | Path = DEFAULT_INPUT,
    output_path: str | Path = DEFAULT_OUTPUT,
    vectorizer_path: str | Path = DEFAULT_VECTORIZER,
    similarity_threshold: float = 0.85,
    include_district: bool = False,
) -> pd.DataFrame:
    """Run duplicate detection and persist project-level results."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(
            f"Master file not found: {input_path}. "
            "Run all cells in notebooks/datapreprocessing.ipynb first."
        )

    projects = pd.read_csv(input_path)
    results, vectorizer = detect_duplicates(
        projects,
        similarity_threshold=similarity_threshold,
        include_district=include_district,
    )
    results["similar_project_id"] = results["similar_project_ids"].map(
        lambda project_ids: project_ids[0] if project_ids else ""
    )
    results = results.drop(columns=["similar_project_ids"])

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_path, index=False)
    save_vectorizer(vectorizer, vectorizer_path)

    print(f"Projects analysed: {len(projects)}")
    print(f"Potential duplicates: {int(results['potential_duplicate_flag'].sum())}")
    print(f"Output: {output_path}")
    print(f"Vectorizer: {vectorizer_path}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--vectorizer", type=Path, default=DEFAULT_VECTORIZER)
    parser.add_argument("--threshold", type=float, default=0.85)
    parser.add_argument("--include-district", action="store_true")
    args = parser.parse_args()
    run_duplicate_detection(
        input_path=args.input,
        output_path=args.output,
        vectorizer_path=args.vectorizer,
        similarity_threshold=args.threshold,
        include_district=args.include_district,
    )


if __name__ == "__main__":
    main()
