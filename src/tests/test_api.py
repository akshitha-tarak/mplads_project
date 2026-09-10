from fastapi.testclient import TestClient

import src.api.main as api_main
from src.api.main import app
from src.tests.test_data_store import _write_sample


def test_api_list_filter_and_detail(tmp_path, monkeypatch):
    sample = _write_sample(tmp_path)
    monkeypatch.setattr(api_main, "DataStore", lambda: sample)

    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["projects"] == 2

        summary = client.get("/risk-summary")
        assert summary.status_code == 200
        assert summary.json()["high_risk"] == 1

        listed = client.get("/projects", params={"risk_level": "HIGH"})
        assert listed.status_code == 200
        body = listed.json()
        assert body["total"] == 1
        project_id = body["items"][0]["project_id"]

        detail = client.get(f"/projects/{project_id}")
        assert detail.status_code == 200
        assert detail.json()["recommended_action"] == "Prioritize for human verification."

        score = client.get(f"/risk-score/{project_id}")
        assert score.status_code == 200
        assert score.json()["risk_score"] == 85

        missing = client.get("/projects/WS/MP9/2024-2025/999")
        assert missing.status_code == 404

        bad = client.get("/projects", params={"alert_type": "not-a-flag"})
        assert bad.status_code == 400

        filters = client.get("/filters")
        assert "Gujarat" in filters.json()["states"]


def test_alerts_default_to_high(tmp_path, monkeypatch):
    sample = _write_sample(tmp_path)
    monkeypatch.setattr(api_main, "DataStore", lambda: sample)

    with TestClient(app) as client:
        alerts = client.get("/alerts")
        assert alerts.status_code == 200
        assert alerts.json()["total"] == 1
