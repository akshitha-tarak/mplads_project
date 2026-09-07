import pandas as pd
import re

df = pd.read_csv(
    "data/cleaned/Works Sanctioned_clean.csv"
)

df["project_id"] = df["work"].str.extract(
    r'(WS/\s*MP\d+/\d{4}-\d{4}/\d+)'
)

print(df[["work", "project_id"]].head())