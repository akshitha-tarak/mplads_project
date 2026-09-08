import pandas as pd

# ==========================
# Load Outputs
# ==========================

iso = pd.read_csv(
    "src/anomaly_detection/outputs/isolation_forest_results.csv"
)

zscore = pd.read_csv(
    "src/anomaly_detection/outputs/zscore_results.csv"
)

iqr = pd.read_csv(
    "src/anomaly_detection/outputs/iqr_results.csv"
)

dup = pd.read_csv(
    "src/anomaly_detection/outputs/duplicate_detection_optimized.csv"
)

# ==========================
# Isolation Forest
# ==========================

iso_df = iso[
    [
        "project_id",
        "cost_anomaly_flag",
        "anomaly_score",
        "anomaly_reason"
    ]
].copy()

iso_df.rename(
    columns={
        "cost_anomaly_flag":
        "isolation_forest_flag"
    },
    inplace=True
)

# ==========================
# Z Score
# ==========================

zscore_df = zscore[
    ["project_id"]
].copy()

zscore_df["zscore_flag"] = 1

# ==========================
# IQR
# ==========================

iqr_df = iqr[
    ["project_id"]
].copy()

iqr_df["iqr_flag"] = 1

# ==========================
# Duplicate Detection
# ==========================

dup_df = (
    dup.groupby("project_id")
    .agg(
        similarity_score=(
            "similarity_score",
            "max"
        )
    )
    .reset_index()
)

dup_df["duplicate_flag"] = 1

# ==========================
# Merge
# ==========================

final_df = iso_df.copy()

final_df = final_df.merge(
    zscore_df,
    on="project_id",
    how="left"
)

final_df = final_df.merge(
    iqr_df,
    on="project_id",
    how="left"
)

final_df = final_df.merge(
    dup_df,
    on="project_id",
    how="left"
)

# ==========================
# Fill Missing Flags
# ==========================

for col in [
    "zscore_flag",
    "iqr_flag",
    "duplicate_flag"
]:
    final_df[col] = (
        final_df[col]
        .fillna(0)
        .astype(int)
    )

final_df["similarity_score"] = (
    final_df["similarity_score"]
    .fillna(0)
)

# ==========================
# ML Risk Score
# ==========================

final_df["ml_risk_score"] = (
      final_df["isolation_forest_flag"] * 40
    + final_df["zscore_flag"] * 25
    + final_df["iqr_flag"] * 20
    + final_df["duplicate_flag"] * 15
)

final_df["ml_risk_score"] = (
    final_df["ml_risk_score"]
    .clip(0, 100)
)

# ==========================
# Save
# ==========================

def get_ml_risk_level(score):

    if score >= 80:
        return "Critical"

    elif score >= 50:
        return "High"

    elif score >= 20:
        return "Medium"

    elif score > 0:
        return "Low"

    return "Normal"

final_df["ml_risk_level"] = (
    final_df["ml_risk_score"]
    .apply(get_ml_risk_level)
)

final_df.to_csv(
    "src/anomaly_detection/outputs/final_ml_output.csv",
    index=False
)

print("\nProjects:", len(final_df))

print(
    "\nHigh Risk Projects:"
)

print(
    final_df.sort_values(
        "ml_risk_score",
        ascending=False
    ).head(20)
)

print(
    "\nSaved: final_ml_output.csv"
)
