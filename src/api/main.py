"""FastAPI application for MPLADS risk monitoring (M4).

Run from the project root:

    uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000

Docs: http://127.0.0.1:8000/docs
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.api.data_store import DataStore, row_to_detail, row_to_list_item
from src.api.schemas import (
    ALERT_TYPE_FLAGS,
    AnalyzeResponse,
    FilterOptions,
    ProjectDetail,
    ProjectListResponse,
    RiskScoreResponse,
    RiskSummary,
)

store: DataStore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global store
    store = DataStore()
    yield
    store = None


app = FastAPI(
    title="MPLADS Risk Monitoring API",
    description=(
        "Decision-support API for MPLADS anomaly and risk indicators. "
        "Flags are for human verification; they do not confirm fraud."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _require_store() -> DataStore:
    if store is None:
        raise HTTPException(status_code=503, detail="Data store is not loaded.")
    return store


@app.get("/health")
def health():
    current = _require_store()
    return {"status": "ok", "projects": int(len(current.df))}


@app.get("/filters", response_model=FilterOptions)
def get_filters(state: str | None = Query(default=None, description="If set, districts are limited to this state.")):
    return _require_store().filter_options(state=state)


@app.get("/risk-summary", response_model=RiskSummary)
def get_risk_summary():
    return _require_store().summary()


@app.get("/projects", response_model=ProjectListResponse)
def list_projects(
    state: str | None = None,
    district: str | None = None,
    constituency: str | None = None,
    work_type: str | None = None,
    work_category: str | None = None,
    risk_level: str | None = Query(default=None, description="LOW, MEDIUM, or HIGH"),
    alert_type: str | None = Query(
        default=None,
        description=f"One of: {', '.join(sorted(ALERT_TYPE_FLAGS))}",
    ),
    min_cost: float | None = None,
    max_cost: float | None = None,
    min_score: int | None = Query(default=None, ge=0, le=100),
    max_score: int | None = Query(default=None, ge=0, le=100),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
):
    current = _require_store()
    try:
        total, page = current.list_projects(
            offset=offset,
            limit=limit,
            state=state,
            district=district,
            constituency=constituency,
            work_type=work_type,
            work_category=work_category,
            risk_level=risk_level,
            alert_type=alert_type,
            min_cost=min_cost,
            max_cost=max_cost,
            min_score=min_score,
            max_score=max_score,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [row_to_list_item(row) for _, row in page.iterrows()],
    }


@app.get("/alerts", response_model=ProjectListResponse)
def list_alerts(
    risk_level: str | None = Query(default="HIGH", description="HIGH, MEDIUM, or omit via risk_level="),
    alert_type: str | None = None,
    state: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Projects that need review. Defaults to HIGH risk."""
    current = _require_store()
    try:
        total, page = current.list_projects(
            offset=offset,
            limit=limit,
            state=state,
            risk_level=risk_level,
            alert_type=alert_type,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [row_to_list_item(row) for _, row in page.iterrows()],
    }


@app.get("/risk-score/{project_id:path}", response_model=RiskScoreResponse)
def get_risk_score(project_id: str):
    row = _require_store().get_project(project_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    item = row_to_detail(row)
    return {
        "project_id": item["project_id"],
        "risk_score": item["risk_score"],
        "risk_level": item["risk_level"],
        "indicators": item["indicators"],
        "explanation": item["explanation"],
        "recommended_action": item["recommended_action"],
    }


@app.get("/projects/{project_id:path}", response_model=ProjectDetail)
def get_project(project_id: str):
    row = _require_store().get_project(project_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    return row_to_detail(row)


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(reload_only: bool = Query(default=True, description="Reload CSVs. Set false only after re-running M2/M3.")):
    """Reload scored CSVs into memory. Does not retrain ML by default."""
    current = _require_store()
    if not reload_only:
        from src.run_pipeline import run_pipeline

        try:
            run_pipeline(skip_ml=True)
        except FileNotFoundError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=f"Pipeline failed: {error}") from error
    try:
        total = current.reload()
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    return {
        "status": "ok",
        "message": "Reloaded scored project data from disk.",
        "total_projects": total,
    }
