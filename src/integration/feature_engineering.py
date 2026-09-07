import pandas as pd

# Load master dataset
df = pd.read_csv("data/cleaned/master_projects.csv")

print("Original Shape:", df.shape)

# --------------------------------------------------
# Convert Dates
# --------------------------------------------------

date_columns = [
    "recommended_date",
    "sanction_date",
    "completion_date",
    "latest_payment_date"
]

for col in date_columns:
    if col in df.columns:
        df[col] = pd.to_datetime(
            df[col],
            errors="coerce",
            dayfirst=True
        )

# --------------------------------------------------
# Completed Flag
# --------------------------------------------------

df["completed_flag"] = (
    df["completion_date"]
    .notna()
    .astype(int)
)

# --------------------------------------------------
# Fill Missing Numeric Values
# --------------------------------------------------

numeric_cols = [
    "recommended_amount____₹_",
    "sanction_amount__₹_",
    "amount_disbursed__₹_",
    "total_expenditure",
    "payment_count"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

# --------------------------------------------------
# Fund Utilization
# --------------------------------------------------

df["fund_utilization"] = (
    df["total_expenditure"] /
    df["sanction_amount__₹_"]
)

# --------------------------------------------------
# Expenditure Ratio
# --------------------------------------------------

df["expenditure_ratio"] = (
    df["total_expenditure"] /
    df["recommended_amount____₹_"]
)

# --------------------------------------------------
# Project Age (Days)
# --------------------------------------------------

today = pd.Timestamp.today()

df["project_age_days"] = (
    today - df["sanction_date"]
).dt.days

# --------------------------------------------------
# Over Budget Flag
# --------------------------------------------------

df["over_budget"] = (
    df["total_expenditure"] >
    df["sanction_amount__₹_"]
).astype(int)

# --------------------------------------------------
# Missing Completion Flag
# --------------------------------------------------

df["missing_completion"] = (
    df["completion_date"]
    .isna()
    .astype(int)
)

# --------------------------------------------------
# Save Engineered Dataset
# --------------------------------------------------

print("\nNew Shape:", df.shape)

print("\nNew Features Added:")
print([
    "completed_flag",
    "fund_utilization",
    "expenditure_ratio",
    "project_age_days",
    "over_budget",
    "missing_completion"
])

df.to_csv(
    "data/cleaned/master_projects_features.csv",
    index=False
)

print("\nFeature Engineering Complete")
print("Saved: data/cleaned/master_projects_features.csv")