import pandas as pd
import os

RAW_FOLDER = "data/raw"
CLEAN_FOLDER = "data/cleaned"

os.makedirs(CLEAN_FOLDER, exist_ok=True)

files = [
    "Works Recommended.csv",
    "Works Sanctioned.csv",
    "Works Completed.csv",
    "Expenditure on Completed and On-going Works as on Date.csv",
    "Amount consented for Calamity.csv"
]

for file in files:

    print(f"\nCleaning {file}")

    path = os.path.join(RAW_FOLDER, file)

    df = pd.read_csv(path)

    # Standardize columns
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
    )

    # Remove duplicate rows
    df = df.drop_duplicates()

    # Clean text columns
    for col in df.select_dtypes(include=["object", "string"]).columns:

        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.replace("\t", "", regex=False)
            .str.replace("\n", "", regex=False)
        )

    if "work" in df.columns:

        df["project_id"] = (
            df["work"]
            .str.extract(r'(WS/\s*MP\d+/\d{4}-\d{4}/\d+)')
        )

        df["project_id"] = (
            df["project_id"]
            .str.replace(" ", "", regex=False)
        )

    if "work_id" in df.columns:

        df["project_id"] = (
            df["work_id"]
            .astype(str)
            .str.replace(" ", "", regex=False)
        )

    # Save
    output_name = file.replace(".csv", "_clean.csv")

    df.to_csv(
        os.path.join(CLEAN_FOLDER, output_name),
        index=False
    )