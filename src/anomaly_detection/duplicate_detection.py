import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==========================
# Load Dataset
# ==========================

df = pd.read_csv(
    "data/cleaned/master_projects_features.csv"
)
df = df.head(1000)

# ==========================
# Keep useful rows
# ==========================

df = df[
    df["work_description"].notna()
].copy()

print("Projects:", len(df))

# ==========================
# Text Cleaning
# ==========================

df["clean_text"] = (
    df["work_description"]
    .astype(str)
    .str.lower()
    .str.replace(r"[^a-zA-Z0-9 ]", "", regex=True)
)

# ==========================
# TF-IDF
# ==========================

vectorizer = TfidfVectorizer(
    stop_words="english"
)

tfidf_matrix = vectorizer.fit_transform(
    df["clean_text"]
)

print(
    "TF-IDF Matrix Shape:",
    tfidf_matrix.shape
)

# ==========================
# Cosine Similarity
# ==========================

similarity_matrix = cosine_similarity(
    tfidf_matrix
)

print(
    "Similarity Matrix Shape:",
    similarity_matrix.shape
)

# ==========================
# Find Duplicates
# ==========================

duplicate_pairs = []

threshold = 0.90

for i in range(len(df)):

    for j in range(i + 1, len(df)):

        score = similarity_matrix[i, j]

        if score >= threshold:

            duplicate_pairs.append(
                {
                    "project_id":
                        df.iloc[i]["project_id"],

                    "similar_project_id":
                        df.iloc[j]["project_id"],

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
    "\nPotential Duplicates Found:",
    len(duplicates_df)
)

print(
    duplicates_df.head(20)
)

# ==========================
# Save Results
# ==========================

duplicates_df.to_csv(
    "src/anomaly_detection/outputs/duplicate_detection_results.csv",
    index=False
)

print(
    "\nSaved: duplicate_detection_results.csv"
)