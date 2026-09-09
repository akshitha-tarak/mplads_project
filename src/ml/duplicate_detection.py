"""Exact and TF-IDF-based potential duplicate detection for MPLADS projects."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

REQUIRED_COLUMNS = {"project_id", "state", "work_type"}
TEXT_COLUMNS = ("work_description_clean", "work_description")


def clean_description(value: Any) -> str:
    """Normalize a project description for exact and TF-IDF comparisons."""
    if pd.isna(value):
        return ""
    text = str(value).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _description_column(df: pd.DataFrame) -> str:
    for column in TEXT_COLUMNS:
        if column in df.columns:
            return column
    raise ValueError("Input data must contain work_description_clean or work_description")


def _validate_input(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if df["project_id"].duplicated().any():
        raise ValueError("Input must contain one row per unique project_id")


def _empty_output(project_ids: pd.Series) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "project_id": project_ids,
            "exact_duplicate_flag": False,
            "exact_duplicate_project_ids": [[] for _ in project_ids],
            "potential_duplicate_flag": False,
            "similar_project_ids": [[] for _ in project_ids],
            "similarity_score": 0.0,
            "duplicate_reason": "",
        }
    )


def detect_duplicates(
    projects: pd.DataFrame,
    similarity_threshold: float = 0.85,
    include_district: bool = False,
    vectorizer: TfidfVectorizer | None = None,
) -> tuple[pd.DataFrame, TfidfVectorizer]:
    """Return project-level exact and restricted TF-IDF duplicate indicators."""
    _validate_input(projects)
    if not 0 < similarity_threshold <= 1:
        raise ValueError("similarity_threshold must be between 0 and 1")

    df = projects.copy()
    source_column = _description_column(df)
    df["_description"] = df[source_column].map(clean_description)
    result = _empty_output(df["project_id"])

    exact_group_columns = ["state"]
    if "constituency" in df.columns:
        exact_group_columns.append("constituency")
    exact_group_columns.append("_description")
    exact_groups = df.groupby(exact_group_columns, dropna=False).groups

    project_index = df.index.tolist()
    position_by_index = {index: position for position, index in enumerate(project_index)}
    for indexes in exact_groups.values():
        indexes = list(indexes)
        if len(indexes) < 2 or not df.loc[indexes[0], "_description"]:
            continue
        ids = df.loc[indexes, "project_id"].tolist()
        for index in indexes:
            position = position_by_index[index]
            result.at[position, "exact_duplicate_flag"] = True
            result.at[position, "exact_duplicate_project_ids"] = [
                project_id for project_id in ids if project_id != df.loc[index, "project_id"]
            ]

    if not df["_description"].str.len().gt(0).any():
        return result, vectorizer or TfidfVectorizer()

    if vectorizer is None:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, stop_words="english")
        matrix = vectorizer.fit_transform(df["_description"])
    else:
        matrix = vectorizer.transform(df["_description"])

    group_columns = ["state", "work_type"]
    if include_district and "district" in df.columns:
        group_columns.append("district")

    for _, group in df.groupby(group_columns, dropna=False):
        indexes = group.index.tolist()
        if len(indexes) < 2:
            continue
        scores = cosine_similarity(matrix[indexes], matrix[indexes])
        for row_number, index in enumerate(indexes):
            candidates = [
                (scores[row_number, other_number], other_index)
                for other_number, other_index in enumerate(indexes)
                if other_index != index
                and scores[row_number, other_number] >= similarity_threshold
                and df.loc[index, "_description"]
                and df.loc[other_index, "_description"]
            ]
            if not candidates:
                continue
            candidates.sort(reverse=True)
            best_score = candidates[0][0]
            similar_ids = [df.loc[other_index, "project_id"] for _, other_index in candidates]
            position = position_by_index[index]
            result.at[position, "potential_duplicate_flag"] = True
            result.at[position, "similar_project_ids"] = similar_ids
            result.at[position, "similarity_score"] = round(float(best_score), 4)
            result.at[position, "duplicate_reason"] = (
                f"Description is similar to {', '.join(similar_ids[:3])}."
            )

    result["potential_duplicate_flag"] = (
        result["potential_duplicate_flag"] | result["exact_duplicate_flag"]
    )
    result.loc[result["exact_duplicate_flag"], "duplicate_reason"] = (
        "Exact description duplicate within the same constituency."
    )
    return result, vectorizer


def save_vectorizer(vectorizer: TfidfVectorizer, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, path)


def load_vectorizer(path: str | Path) -> TfidfVectorizer:
    return joblib.load(path)
