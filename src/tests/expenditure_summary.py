import pandas as pd

exp = pd.read_csv(
    "data/cleaned/Expenditure on Completed and On-going Works as on Date_clean.csv"
)

summary = (
    exp.groupby("project_id")
    .agg(
        total_expenditure=(
            "fund_disbursed_amount__₹_",
            "sum"
        ),
        payment_count=(
            "project_id",
            "count"
        ),
        latest_payment_date=(
            "expenditure_date",
            "max"
        )
    )
    .reset_index()
)

print(summary.shape)
print(summary.head())

summary.to_csv(
    "data/cleaned/expenditure_summary.csv",
    index=False
)

print("Expenditure summary created")