
import os
import pandas as pd

INPUT_PATH = "data/cleaned/master_projects.csv"
ML_OUTPUT_PATH = "data/processed/m2_ml_outputs.csv"
OUTPUT_PATH = "data/cleaned/risk_output.csv"

# =========================
# LOAD DATA
# =========================
df = pd.read_csv(INPUT_PATH)
print("Loaded:", df.shape)

# =========================
# STANDARDIZE COLUMN NAMES
# =========================
df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace("₹", "", regex=False)
    .str.replace(" ", "_", regex=False)
    .str.replace("__", "_", regex=False)
)

# =========================
# LOAD & MERGE M2 ML OUTPUTS (cost anomaly + duplicate detection)
# Cast project_id to str on both sides before merging -- a common
# silent-join-failure cause is one side reading project_id as int64
# and the other as object/str, which makes every merge key mismatch
# and every ML column come back NaN with no error raised.
# =========================
df["project_id"] = df["project_id"].astype(str).str.strip()

ml_df = pd.read_csv(ML_OUTPUT_PATH)
ml_df.columns = ml_df.columns.str.strip().str.lower()
ml_df["project_id"] = ml_df["project_id"].astype(str).str.strip()

ml_cols_to_merge = [
    "project_id",
    "exact_duplicate_flag",
    "exact_duplicate_project_ids",
    "potential_duplicate_flag",
    "similarity_score",
    "duplicate_reason",
    "similar_project_id",
    "cost_anomaly_flag",
    "cost_anomaly_score",
    "cost_anomaly_reason",
    "cost_anomaly_available",
]
ml_cols_to_merge = [c for c in ml_cols_to_merge if c in ml_df.columns]

before_rows = len(df)
df = df.merge(ml_df[ml_cols_to_merge], on="project_id", how="left")
print(f"Merged ML outputs: {before_rows} -> {len(df)} rows (should be unchanged)")

unmatched = df["cost_anomaly_available"].isna().sum() if "cost_anomaly_available" in df.columns else None
if unmatched:
    print(f"⚠ {unmatched} rows had no matching project_id in {ML_OUTPUT_PATH} -- check for join-key mismatches")

# =========================
# DATE CONVERSION (REQUIRED)
# =========================
date_cols = ["recommended_date", "sanction_date", "completion_date"]

for col in date_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    else:
        df[col] = pd.NaT

# =========================
# ENSURE REQUIRED NUMERIC COLS
# =========================
num_cols = ["sanction_amount", "total_expenditure", "amount_disbursed", "cost_amount"]

for col in num_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    else:
        df[col] = pd.NA

# =========================
# FIXED DATE
# =========================
AS_OF_DATE = pd.Timestamp("2026-09-08")

# eSAKSHI portal went live 1 Apr 2023. Recommendation/sanction data for
# Lok Sabha MPs before FY2023-24, and ALL Rajya Sabha data before
# FY2023-24, simply isn't on the portal. Rows that predate this are
# expected to have sparse fields -- that's a data-availability gap,
# not a risk signal, so we flag it separately and never score it.
PORTAL_LAUNCH_DATE = pd.Timestamp("2023-04-01")

# =========================
# PROJECT AGE
# =========================
df["project_age_days"] = (AS_OF_DATE - df["sanction_date"]).dt.days

# =========================
# SANCTION DELAY
# =========================
df["sanction_lag_days"] = (df["sanction_date"] - df["recommended_date"]).dt.days
df["sanction_delay_flag"] = (df["sanction_lag_days"] > 45).fillna(False).astype(int)

# =========================
# PRE-PORTAL DATA-AVAILABILITY FLAG (informational, not scored)
# =========================
df["pre_portal_flag"] = (
    (df["sanction_date"] < PORTAL_LAUNCH_DATE)
    | (df["recommended_date"] < PORTAL_LAUNCH_DATE)
).fillna(False).astype(int)

# =========================
# AWAITING-SANCTION FLAG (informational, not scored)
# Recommendation exists but sanction_date is still null -> the work
# simply hasn't reached the sanction stage yet. This is NOT risk; it's
# a lifecycle state, so it carries 0 points, but we surface it so a
# "no flags fired" row can be told apart from "genuinely clean and
# sanctioned" in the dashboard.
# =========================
df["effective_spend"] = df["total_expenditure"].fillna(df["amount_disbursed"])
df["awaiting_sanction_flag"] = (
    df["sanction_date"].isna() &
    df["completion_date"].isna() &
    df["effective_spend"].isna()
).astype(int)

# =========================
# EFFECTIVE SPEND (needed both for over-expenditure and for softening
# the stalled/delay flags below, so compute it once, up front)
# =========================


# Ratio of what's actually been paid out vs what was sanctioned.
# Guard against divide-by-zero / missing sanction amounts.
safe_sanction_amount = df["sanction_amount"].where(df["sanction_amount"] > 0)
df["spend_completion_ratio"] = df["effective_spend"] / safe_sanction_amount

# =========================
# RAW DELAY / STALLED SIGNALS (before the "pending mark" softening)
# =========================
df["delay_days"] = (
    df["completion_date"].fillna(AS_OF_DATE) - df["sanction_date"]
).dt.days
raw_delay_flag = (df["delay_days"] > 365).fillna(False)

raw_stalled_flag = (
    df["completion_date"].isna() & (df["project_age_days"] > 365)
).fillna(False)

# On eSAKSHI, "completed" only gets set once the Implementing Agency
# manually marks the work complete AFTER final payment -- a paperwork
# step that lags behind reality. A project with spend_completion_ratio
# >= 0.95 is very likely physically finished even if it still looks
# "incomplete" in the data, so we soften delay/stalled for those rows
# into a much lighter "pending mark" signal instead of full risk.
near_complete = (df["spend_completion_ratio"] >= 0.95).fillna(False)

pending_mark_flag = (raw_delay_flag | raw_stalled_flag) & near_complete

df["delay_flag"] = (raw_delay_flag & ~pending_mark_flag).astype(int)
df["stalled_flag"] = (raw_stalled_flag & ~pending_mark_flag).astype(int)
df["pending_mark_flag"] = pending_mark_flag.astype(int)

# =========================
# OVER EXPENDITURE
# =========================
df["over_expenditure_flag"] = (
    df["effective_spend"] > df["sanction_amount"]
).fillna(False).astype(int)

# =========================
# INVALID DATE
# =========================
df["invalid_date_flag"] = (
    df["completion_date"] < df["sanction_date"]
).fillna(False).astype(int)

# =========================
# STATUS MISMATCH
# =========================
if "work_status" in df.columns:
    # NOTE: work_status must be checked for notna() explicitly. Without it,
    # a NaN work_status compared with != "work completed" evaluates to True
    # in pandas, so every row with a filled completion_date but a MISSING
    # work_status gets wrongly counted as a mismatch.
    df["status_flag"] = (
        df["completion_date"].notna()
        & df["work_status"].notna()
        & (df["work_status"].str.lower().str.strip() != "work completed")
    ).fillna(False).astype(int)
else:
    df["status_flag"] = 0

# =========================
# LOW AMOUNT
# =========================
df["low_amount_flag"] = (df["cost_amount"] < 250000).fillna(False).astype(int)

# =========================
# ML-BACKED FLAGS (real M2 output, merged in above)
# exact_duplicate_flag / potential_duplicate_flag come as separate
# signals from the ML engineer -- an exact duplicate is much stronger
# evidence than a fuzzy/potential one, so they get different weights
# instead of being collapsed into a single duplicate_flag.
#
# cost_anomaly_flag is only honored where cost_anomaly_available == 1.
# When the ML model didn't have enough data to check a row, treating
# a missing/default flag value as "not anomalous" is fine, but
# treating it as "anomalous" would wrongly penalize rows the model
# never actually evaluated -- so we zero it out explicitly rather
# than relying on fillna(0) alone to get this right.
# =========================
df["exact_duplicate_flag"] = df.get("exact_duplicate_flag", 0)
df["exact_duplicate_flag"] = pd.to_numeric(df["exact_duplicate_flag"], errors="coerce").fillna(0).astype(int)

df["potential_duplicate_flag"] = df.get("potential_duplicate_flag", 0)
df["potential_duplicate_flag"] = pd.to_numeric(df["potential_duplicate_flag"], errors="coerce").fillna(0).astype(int)

df["cost_anomaly_available"] = df.get("cost_anomaly_available", 0)
df["cost_anomaly_available"] = pd.to_numeric(df["cost_anomaly_available"], errors="coerce").fillna(0).astype(int)

df["cost_anomaly_flag"] = df.get("cost_anomaly_flag", 0)
df["cost_anomaly_flag"] = pd.to_numeric(df["cost_anomaly_flag"], errors="coerce").fillna(0).astype(int)
df["cost_anomaly_flag"] = df["cost_anomaly_flag"] * df["cost_anomaly_available"]

# =========================
# RISK SCORE — POINTS, NOT FRACTIONAL WEIGHTS
# Each flag now carries enough weight on its own that a single strong
# signal (e.g. delay_flag) can move a project out of LOW by itself.
# Multiple flags stack additively, capped at 100.
# pre_portal_flag is deliberately excluded here -- it explains missing
# data, it isn't a risk signal on its own.
# =========================
RISK_POINTS = {
    "delay_flag": 35,
    "stalled_flag": 30,
    "over_expenditure_flag": 30,
    "exact_duplicate_flag": 25,
    "status_flag": 20,
    "sanction_delay_flag": 15,
    "invalid_date_flag": 15,
    "cost_anomaly_flag": 15,
    "potential_duplicate_flag": 10,
    "low_amount_flag": 10,
    "pending_mark_flag": 8,
}

df["risk_score"] = 0
for flag, points in RISK_POINTS.items():
    df["risk_score"] = df["risk_score"] + df[flag] * points

df["risk_score"] = df["risk_score"].clip(upper=100)

# =========================
# SEVERE-COMBINATION OVERRIDES -> near-certain HIGH
# =========================

# Strong corruption signal -> HIGH
df.loc[
    (df["delay_flag"] == 1) & (df["over_expenditure_flag"] == 1),
    "risk_score"
] = df["risk_score"].clip(lower=90)

# Exact duplicate work -> HIGH (near-certain double-billing / fraud signal)
# Strong duplicate ONLY if also suspicious
df.loc[
    (df["exact_duplicate_flag"] == 1) &
    (
        (df["over_expenditure_flag"] == 1) |
        (df["delay_flag"] == 1)
    ),
    "risk_score"
] = df["risk_score"].clip(lower=85)

# Otherwise keep it MEDIUM
df.loc[
    (df["exact_duplicate_flag"] == 1) &
    (df["risk_score"] < 60),
    "risk_score"
] = df["risk_score"].clip(lower=55)

# Long stalled projects -> HIGH
df.loc[
    (df["stalled_flag"] == 1) & (df["project_age_days"] > 500),
    "risk_score"
] = df["risk_score"].clip(lower=85)

# Invalid date -> at least MEDIUM
df.loc[
    df["invalid_date_flag"] == 1,
    "risk_score"
] = df["risk_score"].clip(lower=55)

# Status mismatch -> at least MEDIUM
df.loc[
    df["status_flag"] == 1,
    "risk_score"
] = df["risk_score"].clip(lower=50)

df["risk_score"] = df["risk_score"].round(0).astype(int)

# =========================
# RISK LEVEL (re-tuned to match the new point scale)
# =========================
def get_risk_level(score):
    if score >= 65:
        return "HIGH"
    elif score >= 35:
        return "MEDIUM"
    else:
        return "LOW"

df["risk_level"] = df["risk_score"].apply(get_risk_level)

# =========================
# EXPLAINABLE OUTPUT
# =========================
INDICATOR_LABELS = [
    ("delay_flag", "Project delayed beyond 1 year from sanction"),
    ("stalled_flag", "Incomplete and older than 1 year"),
    ("pending_mark_flag", "Expenditure suggests work is finished, but not yet marked complete on the portal"),
    ("sanction_delay_flag", "Sanction took more than 45 days after recommendation"),
    ("over_expenditure_flag", "Expenditure exceeds sanctioned amount"),
    ("invalid_date_flag", "Completion date is before sanction date"),
    ("status_flag", "Work status does not match completion information"),
    ("low_amount_flag", "Cost is below the usual Rs 2.5 lakh guideline"),
    ("cost_anomaly_flag", "Cost anomaly indicated by ML"),
    ("exact_duplicate_flag", "Exact duplicate work indicated by ML"),
    ("potential_duplicate_flag", "Potential similar work indicated by ML"),
    ("pre_portal_flag", "Recommendation/sanction predates the eSAKSHI portal (pre-FY2023-24) — underlying data may be incomplete"),
    ("awaiting_sanction_flag", "Not yet sanctioned — recommended only, execution has not started"),
]

def build_indicators(row):
    items = [
        label
        for col, label in INDICATOR_LABELS
        if col in row and row[col] == 1
    ]
    # Append the ML engineer's own reason text where available, instead of
    # only the generic label above -- this gives a human reviewer the
    # actual "why" (e.g. which project_id it duplicates, by how much)
    # rather than just "duplicate work indicated by ML".
    if row.get("exact_duplicate_flag") == 1 and pd.notna(row.get("duplicate_reason")):
        items.append(f"Duplicate detail: {row['duplicate_reason']}")
    elif row.get("potential_duplicate_flag") == 1 and pd.notna(row.get("duplicate_reason")):
        items.append(f"Duplicate detail: {row['duplicate_reason']}")

    if row.get("cost_anomaly_flag") == 1 and pd.notna(row.get("cost_anomaly_reason")):
        items.append(f"Cost anomaly detail: {row['cost_anomaly_reason']}")

    return items

df["indicators"] = df.apply(build_indicators, axis=1)

df["explanation"] = df["indicators"].apply(
    lambda items: (
        "Flagged because: " + "; ".join(items) + "."
        if items
        else "No rule-based irregularity flagged on available fields."
    )
)

def recommended_action(row):
    if row["awaiting_sanction_flag"] == 1 and row["risk_score"] == 0:
        return "Awaiting sanction — not yet applicable for execution risk."
    elif row["risk_score"] >= 65:
        return "Prioritize for human verification."
    elif row["risk_score"] >= 35:
        return "Review when resources allow."
    else:
        return "Routine monitoring."

df["recommended_action"] = df.apply(recommended_action, axis=1)

df["indicators"] = df["indicators"].apply(lambda items: "; ".join(items))

# =========================
# FINAL OUTPUT COLUMNS
# =========================
output_cols = [
    "project_id",
    "state",
    "district",
    "constituency",
    "work_type",
    "risk_score",
    "risk_level",
    "delay_days",
    "delay_flag",
    "sanction_delay_flag",
    "stalled_flag",
    "pending_mark_flag",
    "over_expenditure_flag",
    "invalid_date_flag",
    "status_flag",
    "low_amount_flag",
    "cost_anomaly_flag",
    "cost_anomaly_score",
    "cost_anomaly_available",
    "cost_anomaly_reason",
    "exact_duplicate_flag",
    "exact_duplicate_project_ids",
    "potential_duplicate_flag",
    "similarity_score",
    "similar_project_id",
    "duplicate_reason",
    "pre_portal_flag",
    "awaiting_sanction_flag",
    "spend_completion_ratio",
    "indicators",
    "explanation",
    "recommended_action",
]
output_cols = [col for col in output_cols if col in df.columns]

final_df = df[output_cols]

# =========================
# SAVE OUTPUT
# =========================
os.makedirs("data/cleaned", exist_ok=True)
final_df.to_csv(OUTPUT_PATH, index=False)

print("\n✅ Rule Engine Completed")
print("Saved:", OUTPUT_PATH)
print("Final Shape:", final_df.shape)

print("\n===== RISK DISTRIBUTION =====")
print(df["risk_level"].value_counts())

print("\n===== PERCENTAGE =====")
print(df["risk_level"].value_counts(normalize=True) * 100)

flags = [
    "delay_flag",
    "sanction_delay_flag",
    "stalled_flag",
    "pending_mark_flag",
    "over_expenditure_flag",
    "invalid_date_flag",
    "status_flag",
    "low_amount_flag",
    "cost_anomaly_flag",
    "exact_duplicate_flag",
    "potential_duplicate_flag",
    "pre_portal_flag",
    "awaiting_sanction_flag",
]

print("\n===== FLAG COUNTS =====")
for col in flags:
    if col in df.columns:
        print(f"{col}: {df[col].sum()}")
