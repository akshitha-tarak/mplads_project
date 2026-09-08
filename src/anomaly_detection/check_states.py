# src/anomaly_detection/check_stats.py

import pandas as pd

df = pd.read_csv(
    "data/cleaned/master_projects_features.csv"
)

features = [
    "fund_utilization",
    "expenditure_ratio",
    "payment_count",
    "project_age_days",
    "over_budget"
]

print(df[features].describe())
print(df[
    [
        "sanction_amount__₹_",
        "total_expenditure",
        "fund_utilization",
        "expenditure_ratio"
    ]
].head(20))
print(
    df["sanction_amount__₹_"].describe()
)

print(
    df["total_expenditure"].describe()
)