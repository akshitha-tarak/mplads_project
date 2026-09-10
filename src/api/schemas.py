"""Request and response models for the M4 API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


ALERT_TYPE_FLAGS = {
    "delay": "delay_flag",
    "stalled": "stalled_flag",
    "pending_mark": "pending_mark_flag",
    "sanction_delay": "sanction_delay_flag",
    "over_expenditure": "over_expenditure_flag",
    "invalid_date": "invalid_date_flag",
    "status_mismatch": "status_flag",
    "low_amount": "low_amount_flag",
    "cost_anomaly": "cost_anomaly_flag",
    "exact_duplicate": "exact_duplicate_flag",
    "potential_duplicate": "potential_duplicate_flag",
}


class ProjectListItem(BaseModel):
    project_id: str
    work_name: str | None = None
    work_type: str | None = None
    state: str | None = None
    district: str | None = None
    constituency: str | None = None
    estimated_cost: float | None = None
    expenditure: float | None = None
    status: str | None = None
    risk_score: int = 0
    risk_level: str = "LOW"
    indicators: list[str] = Field(default_factory=list)
    recommended_action: str | None = None


class ProjectDetail(ProjectListItem):
    mp_name: str | None = None
    ida: str | None = None
    work_category: str | None = None
    recommended_date: str | None = None
    sanction_date: str | None = None
    completion_date: str | None = None
    recommended_amount: float | None = None
    sanctioned_amount: float | None = None
    amount_disbursed: float | None = None
    total_expenditure: float | None = None
    delay_days: float | None = None
    delay_flag: int = 0
    stalled_flag: int = 0
    sanction_delay_flag: int = 0
    over_expenditure_flag: int = 0
    status_flag: int = 0
    cost_anomaly_flag: int = 0
    cost_anomaly_reason: str | None = None
    exact_duplicate_flag: int = 0
    potential_duplicate_flag: int = 0
    similarity_score: float | None = None
    similar_project_id: str | None = None
    duplicate_reason: str | None = None
    explanation: str | None = None


class ProjectListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ProjectListItem]


class RiskScoreResponse(BaseModel):
    project_id: str
    risk_score: int
    risk_level: str
    indicators: list[str]
    explanation: str | None = None
    recommended_action: str | None = None


class RiskSummary(BaseModel):
    total_projects: int
    high_risk: int
    medium_risk: int
    low_risk: int
    delayed_projects: int
    stalled_projects: int
    potential_duplicate_works: int
    cost_anomalies: int
    financial_alerts: int
    risk_distribution: dict[str, int]
    high_risk_by_state: list[dict[str, Any]]


class FilterOptions(BaseModel):
    states: list[str]
    districts: list[str]
    constituencies: list[str]
    work_types: list[str]
    work_categories: list[str]
    risk_levels: list[str]
    alert_types: list[str]


class AnalyzeResponse(BaseModel):
    status: str
    message: str
    total_projects: int
