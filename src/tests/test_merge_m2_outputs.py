import pandas as pd

from src.ml.merge_m2_outputs import merge_m2_outputs


def test_merge_preserves_duplicate_rows_and_marks_anomaly_coverage(tmp_path):
    duplicate_path = tmp_path / "duplicates.csv"
    anomaly_path = tmp_path / "anomalies.csv"
    output_path = tmp_path / "merged.csv"

    pd.DataFrame(
        {
            "project_id": ["P1", "P2"],
            "potential_duplicate_flag": [True, False],
            "similarity_score": [1.0, 0.0],
        }
    ).to_csv(duplicate_path, index=False)
    pd.DataFrame(
        {
            "project_id": ["P1"],
            "cost_anomaly_flag": [1],
            "anomaly_score": [-0.2],
            "anomaly_reason": ["Unusual cost pattern"],
        }
    ).to_csv(anomaly_path, index=False)

    result = merge_m2_outputs(duplicate_path, anomaly_path, output_path)

    assert len(result) == 2
    assert result.loc[result["project_id"] == "P1", "cost_anomaly_available"].item()
    assert not result.loc[result["project_id"] == "P2", "cost_anomaly_available"].item()
    assert pd.isna(result.loc[result["project_id"] == "P2", "cost_anomaly_flag"].item())
    assert output_path.exists()
