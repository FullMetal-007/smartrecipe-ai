import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.schemas import RecipeCandidate, CandidateEvaluation, AIRankingResponse
from backend.input_processor import parse_requirements
from backend.constraint_validator import ConstraintValidator
from backend.ai_ranker import AIRanker


def candidate(name, minutes, ingredients, rank):
    return RecipeCandidate(name=name, minutes=minutes, ingredients=ingredients, description="Test recipe", tags=[], baseline_rank=rank, baseline_similarity_score=0.5)


class SmartRecipeUnitTests(unittest.TestCase):
    def setUp(self):
        self.candidates = [
            candidate("Quick Chicken Rice Bowl", 20, ["chicken", "rice", "spinach"], 1),
            candidate("Slow Chicken Casserole", 60, ["chicken", "cream"], 2),
        ]

    def response(self, selected):
        evaluations = []
        for c in self.candidates:
            evaluations.append(CandidateEvaluation(
                recipe_id=c.recipe_id, recipe_name=c.name,
                ingredient_match_score=80, intent_match_score=90,
                constraint_match_score=100 if c.minutes <= 30 else 20,
                overall_score=90 if c.minutes <= 30 else 45,
                missing_ingredients=[], constraint_violations=[], reason="Mocked test explanation"
            ))
        return AIRankingResponse(selected_recipe_id=selected.recipe_id, candidate_evaluations=evaluations, final_reason="Mocked selection")

    def test_requirement_parser(self):
        req = parse_requirements("I have chicken, rice and spinach. High protein dinner for 2 people under 30 minutes")
        self.assertEqual(req.max_cooking_minutes, 30)
        self.assertEqual(req.servings, 2)
        self.assertIn("chicken", req.required_ingredients)
        self.assertIn("high-protein", req.dietary_preferences)
        self.assertEqual(req.meal_type, "dinner")

    def test_validator_accepts_compliant_candidate(self):
        result = ConstraintValidator().validate(self.response(self.candidates[0]), self.candidates, parse_requirements("Dinner under 30 minutes"))
        self.assertTrue(result.valid)
        self.assertEqual(result.selected_recipe_id, self.candidates[0].recipe_id)

    def test_validator_flags_cooking_time_violation(self):
        result = ConstraintValidator().validate(self.response(self.candidates[1]), self.candidates, parse_requirements("Dinner under 30 minutes"))
        self.assertFalse(result.valid)
        self.assertTrue(any("exceeding" in item for item in result.violations))

    def test_validator_rejects_unknown_candidate(self):
        response = self.response(self.candidates[0]).model_copy(update={"selected_recipe_id": "not_a_candidate"})
        result = ConstraintValidator().validate(response, self.candidates, parse_requirements("Dinner"))
        self.assertFalse(result.valid)

    def test_ranker_requires_gemini_and_does_not_fallback(self):
        ranker = AIRanker()
        with patch("backend.ai_ranker.LLM_PROVIDER", "invalid"):
            with self.assertRaises(RuntimeError):
                ranker.rank_candidates("dinner", self.candidates)

    def test_candidate_ids_are_unique_for_different_names(self):
        self.assertNotEqual(self.candidates[0].recipe_id, self.candidates[1].recipe_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
