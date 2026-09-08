# import pandas as pd

# df = pd.read_csv(
#     "data/cleaned/master_projects_features.csv"
# )

# bad = df[
#     df["total_expenditure"] > 100000000
# ]

# print("Bad Rows:", len(bad))

# print(
#     bad[
#         [
#             "project_id",
#             "total_expenditure",
#             "sanction_amount__₹_"
#         ]
#     ].head(50)
# )

import pandas as pd

exp = pd.read_csv(
    "data/cleaned/Expenditure on Completed and On-going Works as on Date_clean.csv"
)

bad_project = "WS/MP18161/2024-2025/140180"

print(
    exp[exp["project_id"] == bad_project][
        [
            "project_id",
            "fund_disbursed_amount__₹_"
        ]
    ]
)