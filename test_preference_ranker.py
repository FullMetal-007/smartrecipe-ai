from backend.preference_ranker import score_candidates, ingredient_match_lists
from backend.schemas import ParsedRequirements, RecipeCandidate

def recipe(name, ingredients, rank, minutes=20, calories=None, protein=None, tags=None):
    return RecipeCandidate(
        name=name, ingredients=ingredients, baseline_rank=rank, minutes=minutes,
        calories=calories, protein=protein, tags=tags or []
    )

def test_ingredient_match_outweighs_baseline_order():
    requirements = ParsedRequirements(raw_query="I have chicken and eggs", required_ingredients=["chicken", "egg"])
    candidates = [
        recipe("Plain salad", ["lettuce", "cucumber"], 1),
        recipe("Chicken egg skillet", ["chicken breast", "eggs", "pepper"], 15),
        recipe("Egg salad", ["hard-boiled eggs", "mayonnaise"], 4),
    ]
    ranked = score_candidates(candidates, requirements, requirements.raw_query, limit=2)
    assert ranked[0].name == "Chicken egg skillet"
    assert ranked[1].name == "Egg salad"

def test_healthy_easy_preference_favors_quicker_lighter_candidate():
    requirements = ParsedRequirements(raw_query="healthy and easy")
    candidates = [
        recipe("Creamy bake", ["cream", "cheese", "pasta"], 1, minutes=70, calories=800, protein=12),
        recipe("Chicken vegetable skillet", ["chicken", "broccoli"], 8, minutes=20, calories=320, protein=32),
    ]
    ranked = score_candidates(candidates, requirements, requirements.raw_query, limit=1)
    assert ranked[0].name == "Chicken vegetable skillet"

def test_matched_and_absent_requested_ingredients():
    requirements = ParsedRequirements(raw_query="I have chicken and eggs", required_ingredients=["chicken", "egg"])
    candidate = recipe("Chicken salad", ["cooked chicken", "lettuce"], 1)
    matched, absent = ingredient_match_lists(candidate, requirements)
    assert matched == ["chicken"]
    assert absent == ["egg"]

def test_returns_no_more_than_requested_limit():
    candidates = [recipe(f"Recipe {i}", ["rice"], i) for i in range(1, 12)]
    ranked = score_candidates(candidates, ParsedRequirements(raw_query="rice"), "rice", limit=5)
    assert len(ranked) == 5


def test_gemini_provider_exposes_enrichment_method():
    from backend.llm_provider import GeminiProvider
    assert callable(getattr(GeminiProvider, "enrich_candidates", None))


def test_all_requested_ingredients_are_required_before_preference_ranking():
    from backend.preference_ranker import filter_candidates_by_constraints
    requirements = ParsedRequirements(
        raw_query="I have chicken and a few eggs, healthy and easy",
        required_ingredients=["chicken", "egg"],
    )
    candidates = [
        recipe("Egg salad", ["eggs", "mayonnaise"], 1, minutes=10, calories=300, protein=12),
        recipe("One pot chicken", ["chicken thigh", "potatoes", "green beans"], 2, minutes=30, calories=450, protein=30),
        recipe("Chicken and egg skillet", ["chicken thigh", "eggs", "spinach"], 8, minutes=20, calories=350, protein=32),
    ]
    eligible, rejected = filter_candidates_by_constraints(candidates, requirements)
    ranked = score_candidates(eligible, requirements, requirements.raw_query, limit=2)
    assert ranked[0].name == "Chicken and egg skillet"
    assert {c.name for c, _ in rejected} == {"Egg salad", "One pot chicken"}


def test_hard_filter_requires_every_requested_ingredient():
    from backend.preference_ranker import filter_candidates_by_required_ingredients
    requirements = ParsedRequirements(raw_query="chicken and eggs", required_ingredients=["chicken", "egg"])
    candidates = [
        recipe("Chicken only", ["chicken breast", "salt"], 1),
        recipe("Egg only", ["eggs", "mayonnaise"], 2),
        recipe("Chicken and egg skillet", ["chicken thigh", "eggs", "pepper"], 3),
    ]
    accepted, rejected = filter_candidates_by_required_ingredients(candidates, requirements)
    assert [c.name for c in accepted] == ["Chicken and egg skillet"]
    assert {c.name for c, _ in rejected} == {"Chicken only", "Egg only"}

def test_hard_filter_does_not_reject_when_no_ingredients_requested():
    from backend.preference_ranker import filter_candidates_by_required_ingredients
    requirements = ParsedRequirements(raw_query="something healthy", required_ingredients=[])
    candidates = [recipe("Any recipe", ["rice"], 1)]
    accepted, rejected = filter_candidates_by_required_ingredients(candidates, requirements)
    assert accepted == candidates
    assert rejected == []

def test_title_or_tags_do_not_count_as_requested_ingredients():
    from backend.preference_ranker import filter_candidates_by_required_ingredients
    req = ParsedRequirements(raw_query="chicken and eggs", required_ingredients=["chicken", "egg"])
    candidate = RecipeCandidate(name="Chicken and Egg Salad", ingredients=["chicken breast", "lettuce"], tags=["eggs", "breakfast"], baseline_rank=1)
    accepted, rejected = filter_candidates_by_required_ingredients([candidate], req)
    assert accepted == []
    assert rejected[0][1] == ["egg"]

def test_explicit_time_limit_is_a_hard_constraint():
    from backend.preference_ranker import filter_candidates_by_constraints
    req = ParsedRequirements(raw_query="under 20 minutes", max_cooking_minutes=20)
    candidates = [recipe("Fast recipe", ["rice"], 1, minutes=15), recipe("Slow recipe", ["rice"], 2, minutes=45)]
    accepted, rejected = filter_candidates_by_constraints(candidates, req)
    assert [c.name for c in accepted] == ["Fast recipe"]
    assert rejected[0][0].name == "Slow recipe"
    assert "exceeds limit" in rejected[0][1][0]

def test_local_score_breakdown_is_transparent_and_bounded():
    req = ParsedRequirements(raw_query="healthy and easy", required_ingredients=[])
    candidates = [recipe("Quick vegetables", ["spinach", "tomato"], 1, minutes=15, calories=250, protein=10), recipe("Long bake", ["cream", "cheese", "pasta"], 2, minutes=80, calories=800, protein=15)]
    ranked = score_candidates(candidates, req, req.raw_query, limit=2)
    assert all(c.local_suitability_score is not None and 0 <= c.local_suitability_score <= 100 for c in ranked)
    assert all(0 <= sum(c.local_score_breakdown.values()) <= 600 for c in ranked)
    assert set(ranked[0].local_score_breakdown) == {"ingredient_utilisation", "constraint_satisfaction", "cooking_time", "missing_ingredients", "diet_compatibility", "difficulty"}

def test_processed_ingredient_words_do_not_satisfy_whole_ingredient_request():
    from backend.preference_ranker import ingredient_match_lists
    req = ParsedRequirements(raw_query="I have chicken and eggs", required_ingredients=["chicken", "egg"])
    candidate = recipe("Chicken noodle soup", ["chicken broth", "egg noodles", "carrot"], 1)
    matched, missing = ingredient_match_lists(candidate, req)
    assert matched == []
    assert missing == ["chicken", "egg"]


def test_scoring_weights_sum_to_one():
    from backend.preference_ranker import SCORING_WEIGHTS
    assert round(sum(SCORING_WEIGHTS.values()), 10) == 1.0
