import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==========================
# Load Data
# ==========================

df = pd.read_csv(
    "data/cleaned/master_projects_features.csv"
)

df = df[
    df["work_description"].notna()
].copy()

# ==========================
# Clean Text
# ==========================

df["clean_text"] = (
    df["work_description"]
    .astype(str)
    .str.lower()
    .str.replace(
        r"[^a-zA-Z0-9 ]",
        "",
        regex=True
    )
)

# ==========================
# Duplicate Search
# ==========================

duplicate_pairs = []

threshold = 0.95

groups = df.groupby(
    ["state", "constituency", "work_category"]
)

for (state, constituency, category), group in groups:

    # Remove empty descriptions
    group = group[
        group["clean_text"].str.strip() != ""
    ]

    # Need at least 2 projects to compare
    if len(group) < 2:
        continue

    vectorizer = TfidfVectorizer(
    min_df=1
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(
            group["clean_text"]
        )
    except ValueError:
        continue

    similarity_matrix = cosine_similarity(
        tfidf_matrix
    )

    group = group.reset_index(
        drop=True
    )

    for i in range(len(group)):

        for j in range(i + 1, len(group)):

            score = similarity_matrix[i, j]

            if score >= threshold:

                duplicate_pairs.append(
                    {
                        "project_id":
                            group.iloc[i]["project_id"],

                        "similar_project_id":
                            group.iloc[j]["project_id"],

                        "state":
                            state,

                        "work_category":
                            category,

                        "similarity_score":
                            round(score, 4),

                        "potential_duplicate_flag":
                            1
                    }
                )

# ==========================
# Results
# ==========================

duplicates_df = pd.DataFrame(
    duplicate_pairs
)

print(
    "Potential Duplicates:",
    len(duplicates_df)
)

print(
    duplicates_df.head(20)
)

# ==========================
# Save
# ==========================

duplicates_df.to_csv(
    "src/anomaly_detection/outputs/duplicate_detection_optimized.csv",
    index=False
)

print(
    "\nSaved: duplicate_detection_optimized.csv"
)