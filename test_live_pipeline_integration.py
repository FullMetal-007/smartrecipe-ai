"""Optional integration smoke test against the real saved baseline artifacts.
Run with SMARTRECIPE_RUN_LIVE_TESTS=1 to load the large baseline matrix.
"""
import os
import pytest

pytestmark = pytest.mark.skipif(os.getenv("SMARTRECIPE_RUN_LIVE_TESTS") != "1", reason="Loads large baseline model artifacts; opt in explicitly")

def test_chicken_and_egg_request_returns_only_joint_matches():
    from backend.baseline_service import baseline_service
    from backend.input_processor import parse_requirements
    from backend.preference_ranker import filter_candidates_by_constraints, ingredient_match_lists
    query = "I have chicken and a few eggs. I want something healthy and easy to prepare."
    requirements = parse_requirements(query)
    candidates = baseline_service.get_candidates(query, num_candidates=1000)
    eligible, _ = filter_candidates_by_constraints(candidates, requirements)
    assert eligible, "The current baseline candidate pool did not contain a joint chicken and egg match."
    assert all(not ingredient_match_lists(candidate, requirements)[1] for candidate in eligible)
