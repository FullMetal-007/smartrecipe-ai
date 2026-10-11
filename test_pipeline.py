from unittest.mock import patch
from backend.schemas import RecipeCandidate
from backend.pipeline import run_pipeline

def make_candidate(name, ingredients, rank, minutes=20, calories=400, protein=25):
    return RecipeCandidate(name=name, ingredients=ingredients, baseline_rank=rank, minutes=minutes,
                           calories=calories, protein=protein, tags=[], description="Test record")

def test_backend_pipeline_never_displays_recipe_missing_a_required_ingredient():
    query = "I have chicken and eggs. I want something healthy and easy to prepare."
    candidates = [
        make_candidate("Chicken only", ["chicken breast", "salt"], 1),
        make_candidate("Egg salad", ["eggs", "lettuce"], 2),
        make_candidate("Chicken egg skillet", ["chicken thigh", "eggs", "spinach"], 3),
    ]
    with patch("backend.pipeline.baseline_service.get_candidates", return_value=candidates), \
         patch("backend.pipeline.NUM_RETRIEVAL_CANDIDATES", 1000), \
         patch("backend.pipeline.MAX_RETRIEVAL_CANDIDATES", 1000), \
         patch("backend.pipeline.GEMINI_API_KEY", ""), \
         patch("backend.pipeline.log_experiment"):
        result = run_pipeline(query)
    assert [c.name for c in result.final_candidates] == ["Chicken egg skillet"]
    assert all(not __import__("backend.preference_ranker", fromlist=["ingredient_match_lists"]).ingredient_match_lists(c, result.requirements)[1] for c in result.final_candidates)
    assert len(result.rejected_candidates) == 2

def test_backend_pipeline_reports_conflicting_requirements_as_no_match():
    query = "I have chicken and rice but I need a vegan meal."
    candidates = [
        make_candidate("Chicken rice bowl", ["chicken", "rice"], 1),
        make_candidate("Vegan rice bowl", ["rice", "broccoli"], 2),
        make_candidate("Chicken curry", ["chicken", "rice", "milk"], 3),
    ]
    with patch("backend.pipeline.baseline_service.get_candidates", return_value=candidates), \
         patch("backend.pipeline.NUM_RETRIEVAL_CANDIDATES", 1000), \
         patch("backend.pipeline.MAX_RETRIEVAL_CANDIDATES", 1000), \
         patch("backend.pipeline.GEMINI_API_KEY", ""), \
         patch("backend.pipeline.log_experiment"):
        result = run_pipeline(query)
    assert result.final_candidates == []
