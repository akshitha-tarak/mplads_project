import pandas as pd

files = {
    "recommended": "data/raw/Works Recommended.csv",
    "sanctioned": "data/raw/Works Sanctioned.csv",
    "completed": "data/raw/Works Completed.csv",
    "expenditure": "data/raw/Expenditure on Completed and On-going Works as on Date.csv",
    "calamity": "data/raw/Amount consented for Calamity.csv",
    "allocation": "data/raw/allocated.csv"
}

for name, path in files.items():
    print("\n" + "="*80)
    print(f"DATASET: {name.upper()}")
    print("="*80)

    df = pd.read_csv(path)

    print("Script started")

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst 3 Rows:")
    print(df.head(3))

    print("\nMissing Values:")
    print(df.isnull().sum())