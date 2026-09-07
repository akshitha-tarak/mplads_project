import pandas as pd

recommended = pd.read_csv(
    "data/cleaned/Works Recommended_clean.csv"
)

sanctioned = pd.read_csv(
    "data/cleaned/Works Sanctioned_clean.csv"
)

completed = pd.read_csv(
    "data/cleaned/Works Completed_clean.csv"
)

print("Recommended Projects:",
      recommended["project_id"].nunique())

print("Sanctioned Projects:",
      sanctioned["project_id"].nunique())

print("Completed Projects:",
      completed["project_id"].nunique())

common = set(sanctioned["project_id"]).intersection(
    set(completed["project_id"])
)

print("\nCommon Projects:")
print(len(common))