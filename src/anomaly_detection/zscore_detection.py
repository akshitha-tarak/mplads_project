import pandas as pd
import numpy as np
from scipy.stats import zscore

# ==========================
# Load Dataset
# ==========================

df = pd.read_csv(
    "data/cleaned/master_projects_features.csv"
)

# ==========================
# Use only projects having expenditure
# ==========================

model_df = df[
    df["total_expenditure"].notna()
].copy()

print(
    "Projects analysed:",
    len(model_df)
)

# ==========================
# Z-Score
# ==========================

model_df["z_score"] = np.abs(
    zscore(
        model_df["total_expenditure"]
    )
)

threshold = 3

model_df["zscore_anomaly_flag"] = (
    model_df["z_score"] > threshold
).astype(int)

# ==========================
# Results
# ==========================

anomalies = model_df[
    model_df["zscore_anomaly_flag"] == 1
]

print(
    "\nAnomalies Found:",
    len(anomalies)
)

print(
    anomalies[
        [
            "project_id",
            "total_expenditure",
            "z_score"
        ]
    ]
    .sort_values(
        "z_score",
        ascending=False
    )
    .head(20)
)

# ==========================
# Save
# ==========================

anomalies.to_csv(
    "src/anomaly_detection/outputs/zscore_results.csv",
    index=False
)

print(
    "\nSaved: zscore_results.csv"
)