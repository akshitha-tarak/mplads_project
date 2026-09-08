import pandas as pd

# ==========================
# Load Dataset
# ==========================

df = pd.read_csv(
    "data/cleaned/master_projects_features.csv"
)

# ==========================
# Use expenditure projects only
# ==========================

model_df = df[
    df["total_expenditure"].notna()
].copy()

print(
    "Projects analysed:",
    len(model_df)
)

# ==========================
# IQR Calculation
# ==========================

Q1 = model_df[
    "total_expenditure"
].quantile(0.25)

Q3 = model_df[
    "total_expenditure"
].quantile(0.75)

IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

print("\nQ1:", Q1)
print("Q3:", Q3)
print("IQR:", IQR)
print("Upper Bound:", upper_bound)

# ==========================
# Flag Outliers
# ==========================

model_df["iqr_anomaly_flag"] = (
    model_df["total_expenditure"] > upper_bound
).astype(int)

anomalies = model_df[
    model_df["iqr_anomaly_flag"] == 1
]

# ==========================
# Results
# ==========================

print(
    "\nAnomalies Found:",
    len(anomalies)
)

print(
    anomalies[
        [
            "project_id",
            "total_expenditure"
        ]
    ]
    .sort_values(
        "total_expenditure",
        ascending=False
    )
    .head(20)
)

# ==========================
# Save
# ==========================

anomalies.to_csv(
    "src/anomaly_detection/outputs/iqr_results.csv",
    index=False
)

print(
    "\nSaved: iqr_results.csv"
)