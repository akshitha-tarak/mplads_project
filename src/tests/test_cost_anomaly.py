import pandas as pd

from src.ml.cost_anomaly import detect_cost_anomalies


def test_cost_anomaly_uses_peer_fallback_and_skips_missing_cost():
    projects = pd.DataFrame(
        {
            "project_id": [f"P{i}" for i in range(6)],
            "state": ["A", "A", "A", "B", "B", "B"],
            "district": ["D"] * 6,
            "work_type": ["Roads"] * 6,
            "work_category": ["Normal"] * 6,
            "cost_amount": [100, 110, 90, 1000, 1100, None],
        }
    )

    result, _ = detect_cost_anomalies(projects, minimum_peer_size=3, contamination=0.2)

    assert len(result) == 6
    assert result.loc[result["project_id"] == "P5", "cost_anomaly_available"].item() is False
    assert result.loc[result["project_id"] == "P5", "cost_anomaly_flag"].isna().item()
    assert result.loc[result["project_id"] == "P0", "peer_count"].item() == 3
    assert result.loc[result["project_id"] == "P3", "peer_count"].item() == 5
    assert result["cost_deviation_pct"].notna().sum() == 5


def test_cost_anomaly_requires_current_master_columns():
    projects = pd.DataFrame({"project_id": ["P1"], "cost_amount": [100]})

    try:
        detect_cost_anomalies(projects)
    except ValueError as error:
        assert "work_type" in str(error)
    else:
        raise AssertionError("Expected missing-column validation error")
