import pandas as pd
import joblib

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ==========================
# Load Dataset
# ==========================

df = pd.read_csv(
    "data/cleaned/master_projects_features.csv"
)

# ==========================
# Features
# ==========================

features = [
    "fund_utilization",
    "expenditure_ratio",
    "payment_count",
    "project_age_days",
    "over_budget"
]

# ==========================
# Prepare Data
# ==========================

model_df = df[
    df["total_expenditure"].notna()
].copy()

print(
    "Projects used for training:",
    len(model_df)
)

# Dynamic threshold
payment_threshold = (
    model_df["payment_count"]
    .quantile(0.95)
)

print(
    "Payment Threshold:",
    payment_threshold
)

X = model_df[features].copy()

X = X.fillna(0)

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)


# ==========================
# Train Isolation Forest
# ==========================

model = IsolationForest(
    n_estimators=100,
    contamination=0.05,
    random_state=42
)

model.fit(X_scaled)

# ==========================
# Predictions
# ==========================

predictions = model.predict(X_scaled)

model_df["anomaly_prediction"] = predictions

model_df["cost_anomaly_flag"] = (
    model_df["anomaly_prediction"] == -1
).astype(int)

model_df["anomaly_score"] = (
    model.decision_function(X_scaled)
)

# ==========================
# Basic Reason Generation
# ==========================

def get_reason(row):

    reasons = []

    if row["over_budget"] == 1:
        reasons.append(
            "Expenditure exceeds sanctioned amount"
        )

    if row["fund_utilization"] > 1:
        reasons.append(
            "Fund utilization above 100%"
        )

    if row["project_age_days"] > 700:
        reasons.append(
            "Project age unusually high"
        )

    if row["payment_count"] > payment_threshold:
        reasons.append(
            "Unusually high number of payments"
        )

    if len(reasons) == 0:
        reasons.append(
            "Detected by Isolation Forest pattern analysis"
        )

    return "; ".join(reasons)

model_df["anomaly_reason"] = model_df.apply(
    get_reason,
    axis=1
)

# ==========================
# View Results
# ==========================

anomalies = model_df[
    model_df["cost_anomaly_flag"] == 1
].copy()

anomalies = anomalies.sort_values(
    by="anomaly_score"
)

print("\nProjects Analysed:", len(model_df))
print("Anomalies Found:", len(anomalies))

print("\nTop 10 Anomalies\n")

print(
    anomalies[
        [
            "project_id",
            "fund_utilization",
            "expenditure_ratio",
            "payment_count",
            "project_age_days",
            "over_budget",
            "anomaly_score",
            "anomaly_reason"
        ]
    ].head(10)
)

# ==========================
# Save Results
# ==========================

model_df.to_csv(
    "src/anomaly_detection/outputs/isolation_forest_results.csv",
    index=False
)

# ==========================
# Save Model Artifacts
# ==========================

joblib.dump(
    model,
    "src/anomaly_detection/models/isolation_forest.pkl"
)

joblib.dump(
    scaler,
    "src/anomaly_detection/models/scaler.pkl"
)

print("\nSaved: isolation_forest_results.csv")
print("Saved: isolation_forest.pkl")
print("Saved: scaler.pkl")