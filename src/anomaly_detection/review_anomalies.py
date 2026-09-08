import pandas as pd

df = pd.read_csv(
    "src/anomaly_detection/outputs/isolation_forest_results.csv"
)

anomalies = df[
    df["cost_anomaly_flag"] == 1
]

print(
    anomalies[
        [
            "fund_utilization",
            "expenditure_ratio",
            "payment_count",
            "project_age_days",
            "over_budget"
        ]
    ].head(20)
)