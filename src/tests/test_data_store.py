import pandas as pd
import pytest

from src.api.data_store import DataStore, row_to_detail, row_to_list_item


def _write_sample(tmp_path):
    master = pd.DataFrame(
        {
            "project_id": ["WS/MP1/2024-2025/1", "WS/MP1/2024-2025/2"],
            "state": ["Gujarat", "Bihar"],
            "district": ["KHEDA", "ARARIA"],
            "constituency": ["KHEDA", "ARARIA"],
            "mp_name": ["A", "B"],
            "ida": ["KHEDA(IDA)", "ARARIA(IDA)"],
            "work_category": ["Normal/Others", "Normal/Others"],
            "work_type": ["Street lights", "Street lights"],
            "work_description": ["CC road at village X", "Hall at village Y"],
            "work_status": ["Physical Inspection", "Work Completed"],
            "recommended_date": ["2024-10-01", "2024-09-01"],
            "sanction_date": ["2025-03-29", "2024-09-10"],
            "completion_date": ["2025-04-15", None],
            "recommended_amount": [450000.0, 200000.0],
            "sanction_amount": [450000.0, 200000.0],
            "amount_disbursed": [450000.0, None],
            "total_expenditure": [None, None],
            "payment_count": [None, None],
            "cost_amount": [450000.0, 200000.0],
        }
    )
    risk = pd.DataFrame(
        {
            "project_id": ["WS/MP1/2024-2025/1", "WS/MP1/2024-2025/2"],
            "state": ["Gujarat", "Bihar"],
            "district": ["KHEDA", "ARARIA"],
            "constituency": ["KHEDA", "ARARIA"],
            "work_type": ["Street lights", "Street lights"],
            "risk_score": [85, 10],
            "risk_level": ["HIGH", "LOW"],
            "delay_days": [400, None],
            "delay_flag": [1, 0],
            "stalled_flag": [0, 0],
            "potential_duplicate_flag": [1, 0],
            "cost_anomaly_flag": [0, 0],
            "over_expenditure_flag": [0, 0],
            "indicators": [
                "Project delayed beyond 1 year from sanction; Potential similar work indicated by ML",
                "Cost is below the usual Rs 2.5 lakh guideline",
            ],
            "explanation": ["Flagged because: delay.", "Flagged because: low amount."],
            "recommended_action": [
                "Prioritize for human verification.",
                "Routine monitoring.",
            ],
            "similar_project_id": ["WS/MP1/2024-2025/2", None],
            "duplicate_reason": ["Exact description duplicate within the same constituency.", None],
        }
    )
    master_path = tmp_path / "master.csv"
    risk_path = tmp_path / "risk.csv"
    master.to_csv(master_path, index=False)
    risk.to_csv(risk_path, index=False)
    return DataStore(master_path, risk_path)


def test_store_joins_and_filters(tmp_path):
    store = _write_sample(tmp_path)
    assert len(store.df) == 2
    total, page = store.list_projects(offset=0, limit=10, risk_level="HIGH")
    assert total == 1
    assert page.iloc[0]["project_id"] == "WS/MP1/2024-2025/1"

    total, page = store.list_projects(offset=0, limit=10, alert_type="delay")
    assert total == 1

    total, page = store.list_projects(offset=0, limit=10, state="Bihar")
    assert total == 1


def test_unknown_alert_type_raises(tmp_path):
    store = _write_sample(tmp_path)
    with pytest.raises(ValueError, match="Unknown alert_type"):
        store.list_projects(offset=0, limit=10, alert_type="fraud")


def test_row_serializers(tmp_path):
    store = _write_sample(tmp_path)
    row = store.get_project("WS/MP1/2024-2025/1")
    item = row_to_list_item(row)
    assert item["risk_level"] == "HIGH"
    assert "Project delayed beyond 1 year from sanction" in item["indicators"]
    detail = row_to_detail(row)
    assert detail["similar_project_id"] == "WS/MP1/2024-2025/2"
    assert detail["work_name"].startswith("CC road")


def test_summary_counts(tmp_path):
    store = _write_sample(tmp_path)
    summary = store.summary()
    assert summary["total_projects"] == 2
    assert summary["high_risk"] == 1
    assert summary["delayed_projects"] == 1
    assert summary["potential_duplicate_works"] == 1
