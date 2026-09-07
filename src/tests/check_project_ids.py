import pandas as pd

files = [
    "Works Recommended_clean.csv",
    "Works Sanctioned_clean.csv",
    "Works Completed_clean.csv",
    "Expenditure on Completed and On-going Works as on Date_clean.csv"
]

for file in files:

    df = pd.read_csv(f"data/cleaned/{file}")

    print("\n", file)

    print(
        "Project IDs:",
        df["project_id"].notna().sum()
    )

    print(
        "Unique Project IDs:",
        df["project_id"].nunique()
    )