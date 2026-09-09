import pandas as pd

recommended = pd.read_csv(
    "data/cleaned/Works Recommended_clean.csv"
)

sanctioned = pd.read_csv(
    "data/cleaned/Works Sanctioned_clean.csv"
)

completed = pd.read_csv(
    "data/cleaned/Works Completed_clean.csv"
)

expenditure = pd.read_csv(
    "data/cleaned/expenditure_summary.csv"
)

master = sanctioned.merge(
    recommended[
        [
            "project_id",
            "recommended_date",
            "recommended_amount____₹_"
        ]
    ],
    on="project_id",
    how="left"
)

master = master.merge(
    completed[
        [
            "project_id",
            "completion_date",
            "amount_disbursed__₹_"
        ]
    ],
    on="project_id",
    how="left"
)

master = master.merge(
    expenditure,
    on="project_id",
    how="left"
)

# Keep one stable schema for feature engineering, ML, and the rule engine.
# The source exports use slightly different labels for the same fields.
master = master.rename(
    columns={
        "recommended_date_x": "recommended_date",
        "recommended_amount____₹_": "recommended_amount",
        "sanction_amount__₹_": "sanction_amount",
        "amount_disbursed__₹_": "amount_disbursed",
    }
)

if "recommended_date" not in master.columns and "recommended_date_y" in master.columns:
    master = master.rename(columns={"recommended_date_y": "recommended_date"})
elif "recommended_date_y" in master.columns:
    master["recommended_date"] = master["recommended_date"].fillna(master["recommended_date_y"])
    master = master.drop(columns=["recommended_date_y"])

# These aliases make the ML modules usable with the current MPLADS exports.
# No separate work-type, district, or final-cost column is provided, so use
# the closest source fields and retain the originals for auditability.
if "work_type" not in master.columns and "work_category" in master.columns:
    master["work_type"] = master["work_category"]
if "district" not in master.columns and "constituency" in master.columns:
    master["district"] = master["constituency"]
if "cost_amount" not in master.columns and "sanction_amount" in master.columns:
    master["cost_amount"] = master["sanction_amount"]

print("Master Shape:", master.shape)

print(master.head())

master = master.drop_duplicates(subset=["project_id"])

master.to_csv(
    "data/cleaned/master_projects.csv",
    index=False
)

print("Master dataset created")