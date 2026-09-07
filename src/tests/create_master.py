import pandas as pd

df = pd.read_csv("data/cleaned/master_projects.csv")

print("Rows:", len(df))
print("Unique Project IDs:", df["project_id"].nunique())