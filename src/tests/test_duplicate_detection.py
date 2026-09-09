import pandas as pd

from src.ml.duplicate_detection import detect_duplicates


def test_exact_duplicates_are_flagged():
    projects = pd.DataFrame(
        {
            "project_id": ["P1", "P2", "P3"],
            "state": ["KARNATAKA", "KARNATAKA", "KARNATAKA"],
            "constituency": ["DHA", "DHA", "OTHER"],
            "work_type": ["Roads", "Roads", "Buildings"],
            "work_description": [
                "Construction of a road",
                "Construction of a road",
                "Construction of a road",
            ],
        }
    )

    result, _ = detect_duplicates(projects)

    p1 = result.loc[result["project_id"] == "P1"].iloc[0]
    p2 = result.loc[result["project_id"] == "P2"].iloc[0]
    p3 = result.loc[result["project_id"] == "P3"].iloc[0]
    assert p1["exact_duplicate_flag"]
    assert p1["potential_duplicate_flag"]
    assert p2["exact_duplicate_flag"]
    assert not p3["potential_duplicate_flag"]


def test_similar_descriptions_are_restricted_to_same_state_and_work_type():
    projects = pd.DataFrame(
        {
            "project_id": ["P1", "P2", "P3"],
            "state": ["KARNATAKA", "KARNATAKA", "KERALA"],
            "work_type": ["Roads", "Roads", "Roads"],
            "work_description_clean": [
                "construction concrete road village",
                "construction concrete road village improvement",
                "construction concrete road village improvement",
            ],
        }
    )

    result, _ = detect_duplicates(projects, similarity_threshold=0.5)

    p1 = result.loc[result["project_id"] == "P1"].iloc[0]
    assert "P2" in p1["similar_project_ids"]
    assert "P3" not in p1["similar_project_ids"]


def test_empty_descriptions_do_not_create_matches():
    projects = pd.DataFrame(
        {
            "project_id": ["P1", "P2"],
            "state": ["KARNATAKA", "KARNATAKA"],
            "work_type": ["Roads", "Roads"],
            "work_description_clean": [None, None],
        }
    )

    result, _ = detect_duplicates(projects)

    assert not result["potential_duplicate_flag"].any()
