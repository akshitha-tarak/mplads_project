"""Load M1 master + M3 risk output and serve filtered project views."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.api.schemas import ALERT_TYPE_FLAGS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MASTER = PROJECT_ROOT / "data" / "cleaned" / "master_projects.csv"
DEFAULT_RISK = PROJECT_ROOT / "data" / "cleaned" / "risk_output.csv"

MASTER_KEEP = [
    "project_id",
    "state",
    "district",
    "constituency",
    "mp_name",
    "ida",
    "work_category",
    "work_type",
    "work_description",
    "work_status",
    "recommended_date",
    "sanction_date",
    "completion_date",
    "recommended_amount",
    "sanction_amount",
    "amount_disbursed",
    "total_expenditure",
    "payment_count",
    "cost_amount",
]

RISK_DROP_ON_JOIN = [
    "state",
    "district",
    "constituency",
    "work_type",
]


def _clean_id(value) -> str:
    return str(value).strip() if pd.notna(value) else ""


def _to_int_flag(value) -> int:
    if pd.isna(value):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _to_float(value):
    if pd.isna(value):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(number):
        return None
    return number


def _to_str(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text == "" or text.lower() in {"nan", "none", "nat"}:
        return None
    return text


def split_indicators(value) -> list[str]:
    text = _to_str(value)
    if not text:
        return []
    return [part.strip() for part in text.split(";") if part.strip()]


class DataStore:
    """In-memory store for the scored MPLADS project table."""

    def __init__(
        self,
        master_path: str | Path = DEFAULT_MASTER,
        risk_path: str | Path = DEFAULT_RISK,
    ) -> None:
        self.master_path = Path(master_path)
        self.risk_path = Path(risk_path)
        self.df = pd.DataFrame()
        self.reload()

    def reload(self) -> int:
        if not self.master_path.exists():
            raise FileNotFoundError(f"Master file not found: {self.master_path}")
        if not self.risk_path.exists():
            raise FileNotFoundError(f"Risk file not found: {self.risk_path}")

        master = pd.read_csv(self.master_path, dtype={"project_id": str})
        risk = pd.read_csv(self.risk_path, dtype={"project_id": str})
        master["project_id"] = master["project_id"].map(_clean_id)
        risk["project_id"] = risk["project_id"].map(_clean_id)

        master_cols = [col for col in MASTER_KEEP if col in master.columns]
        risk_keep = [col for col in risk.columns if col not in RISK_DROP_ON_JOIN]
        self.df = master[master_cols].merge(
            risk[risk_keep],
            on="project_id",
            how="left",
            validate="one_to_one",
        )
        return len(self.df)

    def _filtered(
        self,
        state: str | None = None,
        district: str | None = None,
        constituency: str | None = None,
        work_type: str | None = None,
        work_category: str | None = None,
        risk_level: str | None = None,
        alert_type: str | None = None,
        min_cost: float | None = None,
        max_cost: float | None = None,
        min_score: int | None = None,
        max_score: int | None = None,
    ) -> pd.DataFrame:
        frame = self.df
        if state:
            frame = frame[frame["state"].astype(str).str.casefold() == state.casefold()]
        if district:
            frame = frame[frame["district"].astype(str).str.casefold() == district.casefold()]
        if constituency:
            frame = frame[frame["constituency"].astype(str).str.casefold() == constituency.casefold()]
        if work_type:
            frame = frame[frame["work_type"].astype(str).str.casefold() == work_type.casefold()]
        if work_category and "work_category" in frame.columns:
            frame = frame[frame["work_category"].astype(str).str.casefold() == work_category.casefold()]
        if risk_level:
            frame = frame[frame["risk_level"].astype(str).str.upper() == risk_level.upper()]
        if alert_type:
            flag_col = ALERT_TYPE_FLAGS.get(alert_type.lower())
            if flag_col is None:
                raise ValueError(
                    f"Unknown alert_type '{alert_type}'. "
                    f"Use one of: {', '.join(ALERT_TYPE_FLAGS)}"
                )
            if flag_col in frame.columns:
                frame = frame[pd.to_numeric(frame[flag_col], errors="coerce").fillna(0) == 1]
        if min_cost is not None and "cost_amount" in frame.columns:
            frame = frame[pd.to_numeric(frame["cost_amount"], errors="coerce") >= min_cost]
        if max_cost is not None and "cost_amount" in frame.columns:
            frame = frame[pd.to_numeric(frame["cost_amount"], errors="coerce") <= max_cost]
        if min_score is not None:
            frame = frame[pd.to_numeric(frame["risk_score"], errors="coerce").fillna(0) >= min_score]
        if max_score is not None:
            frame = frame[pd.to_numeric(frame["risk_score"], errors="coerce").fillna(0) <= max_score]
        return frame

    def list_projects(self, offset: int, limit: int, **filters) -> tuple[int, pd.DataFrame]:
        frame = self._filtered(**filters)
        total = len(frame)
        if "risk_score" in frame.columns:
            frame = frame.sort_values(["risk_score", "project_id"], ascending=[False, True])
        page = frame.iloc[offset : offset + limit]
        return total, page

    def get_project(self, project_id: str) -> pd.Series | None:
        matches = self.df[self.df["project_id"] == _clean_id(project_id)]
        if matches.empty:
            return None
        return matches.iloc[0]

    def summary(self) -> dict:
        frame = self.df
        levels = (
            frame["risk_level"].astype(str).str.upper().value_counts().to_dict()
            if "risk_level" in frame.columns
            else {}
        )
        high = (
            frame[frame["risk_level"].astype(str).str.upper() == "HIGH"]
            if "risk_level" in frame.columns
            else frame.iloc[0:0]
        )
        by_state = (
            high.groupby(high["state"].astype(str))
            .size()
            .sort_values(ascending=False)
            .head(10)
        )
        return {
            "total_projects": int(len(frame)),
            "high_risk": int(levels.get("HIGH", 0)),
            "medium_risk": int(levels.get("MEDIUM", 0)),
            "low_risk": int(levels.get("LOW", 0)),
            "delayed_projects": int(pd.to_numeric(frame.get("delay_flag"), errors="coerce").fillna(0).sum()),
            "stalled_projects": int(pd.to_numeric(frame.get("stalled_flag"), errors="coerce").fillna(0).sum()),
            "potential_duplicate_works": int(
                pd.to_numeric(frame.get("potential_duplicate_flag"), errors="coerce").fillna(0).sum()
            ),
            "cost_anomalies": int(pd.to_numeric(frame.get("cost_anomaly_flag"), errors="coerce").fillna(0).sum()),
            "financial_alerts": int(
                pd.to_numeric(frame.get("over_expenditure_flag"), errors="coerce").fillna(0).sum()
            ),
            "risk_distribution": {
                "HIGH": int(levels.get("HIGH", 0)),
                "MEDIUM": int(levels.get("MEDIUM", 0)),
                "LOW": int(levels.get("LOW", 0)),
            },
            "high_risk_by_state": [
                {"state": state, "count": int(count)} for state, count in by_state.items()
            ],
        }

    def filter_options(self, state: str | None = None) -> dict:
        frame = self.df
        if state:
            frame = frame[frame["state"].astype(str).str.casefold() == state.casefold()]

        def unique(column: str) -> list[str]:
            if column not in frame.columns:
                return []
            values = frame[column].dropna().astype(str).str.strip()
            values = values[~values.str.lower().isin({"", "nan", "none"})]
            return sorted(values.unique().tolist())

        return {
            "states": unique("state"),
            "districts": unique("district"),
            "constituencies": unique("constituency"),
            "work_types": unique("work_type"),
            "work_categories": unique("work_category"),
            "risk_levels": ["LOW", "MEDIUM", "HIGH"],
            "alert_types": sorted(ALERT_TYPE_FLAGS.keys()),
        }


def row_to_list_item(row: pd.Series) -> dict:
    return {
        "project_id": _clean_id(row.get("project_id")),
        "work_name": _to_str(row.get("work_description")) or _to_str(row.get("work_type")),
        "work_type": _to_str(row.get("work_type")),
        "state": _to_str(row.get("state")),
        "district": _to_str(row.get("district")),
        "constituency": _to_str(row.get("constituency")),
        "estimated_cost": _to_float(row.get("cost_amount")),
        "expenditure": _to_float(row.get("total_expenditure")) or _to_float(row.get("amount_disbursed")),
        "status": _to_str(row.get("work_status")),
        "risk_score": _to_int_flag(row.get("risk_score")),
        "risk_level": (_to_str(row.get("risk_level")) or "LOW").upper(),
        "indicators": split_indicators(row.get("indicators")),
        "recommended_action": _to_str(row.get("recommended_action")),
    }


def row_to_detail(row: pd.Series) -> dict:
    item = row_to_list_item(row)
    item.update(
        {
            "mp_name": _to_str(row.get("mp_name")),
            "ida": _to_str(row.get("ida")),
            "work_category": _to_str(row.get("work_category")),
            "recommended_date": _to_str(row.get("recommended_date")),
            "sanction_date": _to_str(row.get("sanction_date")),
            "completion_date": _to_str(row.get("completion_date")),
            "recommended_amount": _to_float(row.get("recommended_amount")),
            "sanctioned_amount": _to_float(row.get("sanction_amount")),
            "amount_disbursed": _to_float(row.get("amount_disbursed")),
            "total_expenditure": _to_float(row.get("total_expenditure")),
            "delay_days": _to_float(row.get("delay_days")),
            "delay_flag": _to_int_flag(row.get("delay_flag")),
            "stalled_flag": _to_int_flag(row.get("stalled_flag")),
            "sanction_delay_flag": _to_int_flag(row.get("sanction_delay_flag")),
            "over_expenditure_flag": _to_int_flag(row.get("over_expenditure_flag")),
            "status_flag": _to_int_flag(row.get("status_flag")),
            "cost_anomaly_flag": _to_int_flag(row.get("cost_anomaly_flag")),
            "cost_anomaly_reason": _to_str(row.get("cost_anomaly_reason")),
            "exact_duplicate_flag": _to_int_flag(row.get("exact_duplicate_flag")),
            "potential_duplicate_flag": _to_int_flag(row.get("potential_duplicate_flag")),
            "similarity_score": _to_float(row.get("similarity_score")),
            "similar_project_id": _to_str(row.get("similar_project_id")),
            "duplicate_reason": _to_str(row.get("duplicate_reason")),
            "explanation": _to_str(row.get("explanation")),
        }
    )
    return item
