# # # import pandas as pd

# # # df = pd.read_csv(
# # #     "data/cleaned/master_projects_features.csv"
# # # )

# # # # print(df.columns.tolist())
# # import pandas as pd

# # df = pd.read_csv(
# #     "src/anomaly_detection/outputs/duplicate_detection_results.csv"
# # )

# # print(df.head(50))

# # master = pd.read_csv(
# #     "data/cleaned/master_projects_features.csv"
# # )

# # id1 = "WS/MP18144/2024-2025/135750"
# # id2 = "PUT_SECOND_ID_HERE"

# # print(
# #     master.loc[
# #         master["project_id"] == id1,
# #         ["project_id", "work_description", "state"]
# #     ]
# # )

# # print(
# #     master.loc[
# #         master["project_id"] == id2,
# #         ["project_id", "work_description", "state"]
# #     ]
# # )
# import pandas as pd

# pd.set_option("display.max_colwidth", None)

# master = pd.read_csv(
#     "data/cleaned/master_projects_features.csv"
# )

# ids = [
#     "WS/MP18278/2024-2025/135168",
#     "WS/MP18278/2024-2025/135169"
# ]

# print(
#     master.loc[
#         master["project_id"].isin(ids),
#         [
#             "project_id",
#             "work_description",
#             "state",
#             "work_category"
#         ]
#     ].to_string()
# )

import pandas as pd

dup = pd.read_csv(
    "src/anomaly_detection/outputs/duplicate_detection_optimized.csv"
)

print("Unique flagged projects:")
print(dup["project_id"].nunique())

print("\nSimilarity stats:")
print(dup["similarity_score"].describe())