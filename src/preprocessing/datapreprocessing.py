"""Build data/cleaned/master_projects.csv from the four portal extracts.

Converted from notebooks/datapreprocessing.ipynb so M1 lives under src/
like M2, M3, and M4.

Run from the project root:

    python -m src.preprocessing.datapreprocessing
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = PROJECT_ROOT / "dataset"
OUTPUT_PATH = PROJECT_ROOT / "data" / "cleaned" / "master_projects.csv"


def extract_project_id(series: pd.Series) -> pd.Series:
    pid = series.astype(str).str.extract(
        r"(WS/\s*MP\d+/\d{4}-\d{4}/\d+)",
        expand=False,
    )
    return pid.str.replace(r"\s+", "", regex=True)


def extract_work_type(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(r"WS/\s*MP\d+/\d{4}-\d{4}/\d+\s*-?\s*", "", regex=True)
        .str.strip()
    )


def extract_district(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.split("(", n=1)
        .str[0]
        .str.strip()
        .str.upper()
    )


def to_amount(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False),
        errors="coerce",
    )


def _drop_grand_total(frame: pd.DataFrame) -> pd.DataFrame:
    if "Sr. No." in frame.columns:
        return frame[frame["Sr. No."] != "Grand Total"]
    return frame


def build_master_dataset(
    dataset_dir: str | Path = DATASET_DIR,
    output_path: str | Path = OUTPUT_PATH,
) -> pd.DataFrame:
    dataset_dir = Path(dataset_dir)
    output_path = Path(output_path)

    recommended = _drop_grand_total(pd.read_csv(dataset_dir / "Works Recommended.csv"))
    sanctioned = _drop_grand_total(pd.read_csv(dataset_dir / "Works Sanctioned.csv"))
    completed = _drop_grand_total(pd.read_csv(dataset_dir / "Works Completed.csv"))
    expenditure = _drop_grand_total(
        pd.read_csv(dataset_dir / "Expenditure on Completed and On-going Works as on Date.csv")
    )

    recommended = recommended.rename(
        columns={
            "Work category": "work_category",
            "WORK": "work",
            "State": "state",
            "IDA": "ida",
            "Hon'ble Members of Parliament": "mp_name",
            "Constituency": "constituency",
            "Work description": "work_description",
            "Recommended date": "recommended_date",
            "RECOMMENDED AMOUNT   ( ₹ )": "recommended_amount",
            "Sanction Date": "sanction_date",
        }
    ).drop(columns=["Sr. No."], errors="ignore")

    sanctioned = sanctioned.rename(
        columns={
            "Work category": "work_category",
            "Work": "work",
            "State": "state",
            "IDA": "ida",
            "Hon'ble Members of Parliament": "mp_name",
            "Constituency": "constituency",
            "Work description": "work_description",
            "Recommended date": "recommended_date",
            "Sanction Date": "sanction_date",
            "Sanction Amount ( ₹ )": "sanction_amount",
            "Work Status": "work_status",
        }
    ).drop(columns=["Sr. No."], errors="ignore")

    completed = completed.rename(
        columns={
            "Work Category": "work_category",
            "Work": "work",
            "State": "state",
            "IDA": "ida",
            "Work Description": "work_description",
            "Hon'ble Members of Parliament": "mp_name",
            "Constituency": "constituency",
            "Completion Date": "completion_date",
            "Amount Disbursed ( ₹ )": "amount_disbursed",
        }
    ).drop(columns=["Sr. No.", "Image"], errors="ignore")

    expenditure = expenditure.rename(
        columns={
            "State": "state",
            "Work": "work_type",
            "Work ID": "work_id",
            "IDA": "ida",
            "Hon'ble Members of Parliament": "mp_name",
            "Constituency": "constituency",
            "Expenditure Date": "expenditure_date",
            "Vendor Name": "vendor_name",
            "Payment Status": "payment_status",
            "Fund Disbursed Amount ( ₹ )": "fund_disbursed_amount",
        }
    ).drop(columns=["Sr. No."], errors="ignore")

    recommended["project_id"] = extract_project_id(recommended["work"])
    sanctioned["project_id"] = extract_project_id(sanctioned["work"])
    completed["project_id"] = extract_project_id(completed["work"])
    expenditure["project_id"] = (
        expenditure["work_id"].astype(str).str.replace(r"\s+", "", regex=True)
    )

    for frame in (recommended, sanctioned, completed):
        frame["work_type"] = extract_work_type(frame["work"])
        frame["district"] = extract_district(frame["ida"])
    expenditure["district"] = extract_district(expenditure["ida"])

    for frame in (recommended, sanctioned):
        for col in ["recommended_date", "sanction_date"]:
            frame[col] = pd.to_datetime(frame[col], errors="coerce", dayfirst=True)
    completed["completion_date"] = pd.to_datetime(
        completed["completion_date"], errors="coerce", dayfirst=True
    )
    expenditure["expenditure_date"] = pd.to_datetime(
        expenditure["expenditure_date"], errors="coerce", dayfirst=True
    )

    recommended["recommended_amount"] = to_amount(recommended["recommended_amount"])
    sanctioned["sanction_amount"] = to_amount(sanctioned["sanction_amount"])
    completed["amount_disbursed"] = to_amount(completed["amount_disbursed"])
    expenditure["fund_disbursed_amount"] = to_amount(expenditure["fund_disbursed_amount"])

    exp_summary = (
        expenditure.groupby("project_id", as_index=False)
        .agg(
            total_expenditure=("fund_disbursed_amount", "sum"),
            payment_count=("project_id", "count"),
        )
    )

    recommended = recommended[recommended["project_id"].notna()].drop_duplicates("project_id")
    sanctioned = sanctioned[sanctioned["project_id"].notna()].drop_duplicates("project_id")
    completed = completed[completed["project_id"].notna()].drop_duplicates("project_id")
    exp_summary = exp_summary[exp_summary["project_id"].notna()].drop_duplicates("project_id")

    id_cols = [
        "state",
        "district",
        "constituency",
        "mp_name",
        "ida",
        "work_category",
        "work_type",
        "work_description",
    ]
    san_keep = ["project_id"] + id_cols + [
        "recommended_date",
        "sanction_date",
        "sanction_amount",
        "work_status",
    ]
    rec_keep = ["project_id", "recommended_amount"]
    com_keep = ["project_id", "completion_date", "amount_disbursed"] + id_cols
    exp_id_keep = [
        "project_id",
        "state",
        "district",
        "constituency",
        "mp_name",
        "ida",
        "work_type",
    ]

    master = sanctioned[san_keep].merge(recommended[rec_keep], on="project_id", how="outer")
    master = master.merge(completed[com_keep], on="project_id", how="outer", suffixes=("", "_com"))
    for col in id_cols:
        master[col] = master[col].fillna(master[f"{col}_com"])
        master = master.drop(columns=[f"{col}_com"])

    master = master.merge(exp_summary, on="project_id", how="outer")
    exp_id = expenditure.drop_duplicates("project_id")[exp_id_keep]
    master = master.merge(exp_id, on="project_id", how="left", suffixes=("", "_exp"))
    for col in ["state", "district", "constituency", "mp_name", "ida", "work_type"]:
        master[col] = master[col].fillna(master[f"{col}_exp"])
        master = master.drop(columns=[f"{col}_exp"])

    master["cost_amount"] = (
        master["sanction_amount"]
        .fillna(master["recommended_amount"])
        .fillna(master["amount_disbursed"])
        .fillna(master["total_expenditure"])
    )

    col_order = [
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
    master = master[col_order]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(output_path, index=False)
    print("Master saved:", output_path, master.shape)
    return master


def main() -> None:
    build_master_dataset()


if __name__ == "__main__":
    main()
