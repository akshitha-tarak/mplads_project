"""Peer-statistical and Isolation Forest cost anomaly detection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

REQUIRED_COLUMNS = {
    "project_id",
    "state",
    "district",
    "work_type",
    "work_category",
    "cost_amount",
}
CATEGORICAL_COLUMNS = ["work_type", "state", "district", "work_category"]
NUMERIC_COLUMNS = ["log_cost_amount"]


def _validate_input(projects: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS.difference(projects.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if projects["project_id"].duplicated().any():
        raise ValueError("Input must contain one row per unique project_id")


def _as_text(value: Any) -> str:
    return "__missing__" if pd.isna(value) or str(value).strip() == "" else str(value)


def _peer_statistics(projects: pd.DataFrame, minimum_peer_size: int) -> pd.DataFrame:
    eligible = projects[projects["cost_amount"].notna()].copy()
    eligible["_state"] = eligible["state"].map(_as_text)
    eligible["_work_type"] = eligible["work_type"].map(_as_text)
    eligible["_primary_peer"] = eligible["_state"] + "||" + eligible["_work_type"]
    primary_sizes = eligible.groupby("_primary_peer")["project_id"].transform("size")
    eligible["_peer_basis"] = np.where(primary_sizes >= minimum_peer_size, "state_work_type", "work_type")

    def aggregate(grouped: Any) -> pd.DataFrame:
        stats = grouped.agg(
            peer_count="count",
            peer_median_cost="median",
            peer_q1_cost=lambda values: values.quantile(0.25),
            peer_q3_cost=lambda values: values.quantile(0.75),
            peer_std_cost="std",
        ).reset_index()
        stats["peer_iqr_cost"] = stats["peer_q3_cost"] - stats["peer_q1_cost"]
        return stats

    primary_stats = aggregate(eligible.groupby("_primary_peer")["cost_amount"])
    primary_stats = primary_stats.rename(columns={"_primary_peer": "_peer_key"})
    fallback_stats = aggregate(eligible.groupby("_work_type")["cost_amount"])
    fallback_stats = fallback_stats.rename(columns={"_work_type": "_peer_key"})

    eligible["_peer_key"] = np.where(
        eligible["_peer_basis"] == "state_work_type",
        eligible["_primary_peer"],
        eligible["_work_type"],
    )
    eligible["_stats_basis"] = eligible["_peer_basis"]
    primary_stats["_stats_basis"] = "state_work_type"
    fallback_stats["_stats_basis"] = "work_type"
    stats = pd.concat([primary_stats, fallback_stats], ignore_index=True)
    eligible = eligible.merge(
        stats,
        left_on=["_peer_key", "_stats_basis"],
        right_on=["_peer_key", "_stats_basis"],
        how="left",
    )
    eligible["cost_deviation_pct"] = np.where(
        eligible["peer_median_cost"].ne(0),
        (eligible["cost_amount"] - eligible["peer_median_cost"]) / eligible["peer_median_cost"],
        np.nan,
    )
    peer_std = eligible["peer_std_cost"].fillna(0)
    eligible["cost_zscore"] = np.where(
        peer_std.gt(0),
        (eligible["cost_amount"] - eligible["peer_median_cost"]) / peer_std,
        0.0,
    )
    lower = eligible["peer_q1_cost"] - 1.5 * eligible["peer_iqr_cost"]
    upper = eligible["peer_q3_cost"] + 1.5 * eligible["peer_iqr_cost"]
    eligible["cost_iqr_flag"] = (eligible["cost_amount"].lt(lower) | eligible["cost_amount"].gt(upper)).astype(int)
    return eligible


def detect_cost_anomalies(
    projects: pd.DataFrame,
    minimum_peer_size: int = 20,
    contamination: float = 0.05,
    random_state: int = 42,
) -> tuple[pd.DataFrame, Pipeline]:
    """Return one cost-anomaly result row per project and the fitted model."""
    _validate_input(projects)
    if minimum_peer_size < 2:
        raise ValueError("minimum_peer_size must be at least 2")

    results = projects[["project_id"]].copy()
    eligible = _peer_statistics(projects, minimum_peer_size)
    if eligible.empty:
        for column in ["peer_count", "peer_median_cost", "peer_iqr_cost", "cost_deviation_pct", "cost_zscore", "cost_iqr_flag", "cost_anomaly_flag", "cost_anomaly_score"]:
            results[column] = np.nan
        results["cost_anomaly_reason"] = "Missing cost_amount; not analyzed."
        results["cost_anomaly_available"] = False
        return results, Pipeline([])

    model_data = eligible.copy()
    model_data["log_cost_amount"] = np.log1p(model_data["cost_amount"])
    for column in CATEGORICAL_COLUMNS:
        model_data[column] = model_data[column].map(_as_text)

    preprocessor = ColumnTransformer(
        [
            ("numeric", "passthrough", NUMERIC_COLUMNS),
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_COLUMNS),
        ]
    )
    model = Pipeline(
        [
            ("preprocess", preprocessor),
            ("isolation_forest", IsolationForest(contamination=contamination, random_state=random_state, n_estimators=200)),
        ]
    )
    model.fit(model_data[NUMERIC_COLUMNS + CATEGORICAL_COLUMNS])
    predictions = model.predict(model_data[NUMERIC_COLUMNS + CATEGORICAL_COLUMNS])
    model_scores = -model.decision_function(model_data[NUMERIC_COLUMNS + CATEGORICAL_COLUMNS])
    eligible["cost_anomaly_flag"] = (predictions == -1).astype(int)
    eligible["cost_anomaly_score"] = model_scores

    def reason(row: pd.Series) -> str:
        reasons = []
        if row["cost_iqr_flag"]:
            reasons.append("Outside the peer-group IQR")
        if abs(row["cost_zscore"]) >= 3:
            reasons.append("Large peer-group z-score")
        if row["cost_deviation_pct"] >= 1:
            reasons.append("Cost is at least twice the peer median")
        if row["cost_anomaly_flag"] and not reasons:
            reasons.append("Detected by Isolation Forest pattern analysis")
        return "; ".join(reasons)

    eligible["cost_anomaly_reason"] = eligible.apply(reason, axis=1)
    output_columns = [
        "project_id", "peer_count", "peer_median_cost", "peer_iqr_cost",
        "cost_deviation_pct", "cost_zscore", "cost_iqr_flag", "cost_anomaly_flag",
        "cost_anomaly_score", "cost_anomaly_reason",
    ]
    results = results.merge(eligible[output_columns], on="project_id", how="left", validate="one_to_one")
    results["cost_anomaly_available"] = results["cost_anomaly_flag"].notna()
    results.loc[~results["cost_anomaly_available"], "cost_anomaly_reason"] = "Missing cost_amount; not analyzed."
    return results, model


def save_model(model: Pipeline, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
