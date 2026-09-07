import pandas as pd

files = [
    "Works Recommended_clean.csv",
    "Works Sanctioned_clean.csv",
    "Works Completed_clean.csv",
    "Expenditure on Completed and On-going Works as on Date_clean.csv"
]

for file in files:

    df = pd.read_csv(f"data/cleaned/{file}")

    print("\n" + "="*80)
    print(file)

    print("Rows:", len(df))

    if "work" in df.columns:
        print("Unique Work:", df["work"].nunique())

    if "work_id" in df.columns:
        print("Unique Work ID:", df["work_id"].nunique())

    df.rename(columns={
    "recommended_amount____₹_": "recommended_amount",
    "sanction_amount__₹_": "sanction_amount",
    "amount_disbursed__₹_": "amount_disbursed",
    "fund_disbursed_amount__₹_": "fund_disbursed_amount",
    "consent_amount__₹_": "consent_amount",
    "hon'ble_members_of_parliament": "mp_name"
}, inplace=True)