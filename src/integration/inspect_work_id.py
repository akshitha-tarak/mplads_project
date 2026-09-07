import pandas as pd

df = pd.read_csv(
    "data/cleaned/Expenditure on Completed and On-going Works as on Date_clean.csv"
)

print(df[["work", "work_id"]].head(20))

print("\nUnique Works:", df["work"].nunique())
print("Unique Work IDs:", df["work_id"].nunique())