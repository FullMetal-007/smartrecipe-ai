"""Deterministic validation of model output against dataset facts and user constraints.
These checks are conservative and are not a certified allergy, diet, or food-safety guarantee.
"""
from typing import List
from backend.schemas import AIRankingResponse, ParsedRequirements, RecipeCandidate, ValidationResult
from backend.preference_ranker import ingredient_match_lists, _diet_violations

class ConstraintValidator:
    def validate(self, ai_response: AIRankingResponse, candidates: List[RecipeCandidate], requirements: ParsedRequirements) -> ValidationResult:
        violations, warnings = [], []
        by_id = {c.recipe_id: c for c in candidates}
        selected = by_id.get(ai_response.selected_recipe_id)
        if selected is None:
            return ValidationResult(valid=False, violations=["Selected recipe is not one of the supplied baseline candidates."], warnings=[])
        evaluations = {e.recipe_id: e for e in ai_response.candidate_evaluations}
        if set(evaluations) != set(by_id):
            violations.append("AI evaluations do not correspond exactly to the supplied candidate set.")
        selected_eval = evaluations.get(selected.recipe_id)
        if selected_eval and selected_eval.recipe_name != selected.name:
            violations.append("AI recipe name does not match the dataset record.")
        if requirements.max_cooking_minutes is not None:
            if selected.minutes > requirements.max_cooking_minutes:
                violations.append(f"Selected recipe takes {selected.minutes} minutes, exceeding the requested {requirements.max_cooking_minutes} minutes.")
            elif selected.minutes <= 0:
                warnings.append("Dataset cooking time is unavailable, so the time limit cannot be verified.")
        _, absent = ingredient_match_lists(selected, requirements)
        if absent:
            violations.append("Selected recipe is missing requested ingredients: " + ", ".join(absent))
        violations.extend(_diet_violations(selected, requirements))
        if "high-protein" in requirements.dietary_preferences and selected.protein is None:
            warnings.append("Protein nutrition data is unavailable, so high-protein suitability cannot be verified.")
        if "low-carb" in requirements.dietary_preferences or "keto" in requirements.dietary_preferences:
            warnings.append("Carbohydrate metadata is not available consistently; low-carb or keto suitability is not certified.")
        return ValidationResult(valid=not violations, violations=violations, warnings=warnings, selected_recipe_id=selected.recipe_id)

constraint_validator = ConstraintValidator()
