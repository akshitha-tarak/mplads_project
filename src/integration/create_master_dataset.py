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

print("Master Shape:", master.shape)

print(master.head())

master = master.drop_duplicates(subset=["project_id"])

master.to_csv(
    "data/cleaned/master_projects.csv",
    index=False
)

print("Master dataset created")