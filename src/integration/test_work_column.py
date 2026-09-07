import pandas as pd

df = pd.read_csv(
    "data/cleaned/Works Sanctioned_clean.csv"
)

print(df["work"].head(10).tolist())