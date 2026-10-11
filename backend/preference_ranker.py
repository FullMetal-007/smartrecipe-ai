"""Transparent local scoring and hard constraint gates layered around baseline retrieval.

The baseline retrieval algorithm and its pickle artifacts are not modified.
Scoring weights are documented in docs/evaluation_protocol.md and remain configurable
in this module for reproducible experiments.
"""
from __future__ import annotations
import re
from typing import List, Sequence, Tuple
from backend.input_processor import INGREDIENT_ALIASES
from backend.schemas import ParsedRequirements, RecipeCandidate

SCORING_WEIGHTS = {
    "ingredient_utilisation": 0.30,
    "constraint_satisfaction": 0.30,
    "cooking_time": 0.15,
    "missing_ingredients": 0.10,
    "diet_compatibility": 0.10,
    "difficulty": 0.05,
}
PANTRY_STAPLES = {"salt", "pepper", "black pepper", "water", "olive oil", "vegetable oil", "oil", "cooking oil"}
MEAT_TERMS = ("chicken", "beef", "pork", "lamb", "turkey", "bacon", "ham", "fish", "salmon", "tuna", "shrimp", "prawn", "crab", "lobster", "sausage", "steak", "duck")
DAIRY_TERMS = ("milk", "cheese", "butter", "cream", "yogurt", "yoghurt", "whey", "ghee", "mozzarella", "parmesan", "cheddar")
GLUTEN_TERMS = ("flour", "bread", "pasta", "wheat", "barley", "rye", "semolina", "couscous", "spelt")


def _contains(text: str, phrase: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(phrase.lower()) + r"(?!\w)", text.lower()))


def _ingredient_match(candidate: RecipeCandidate, canonical: str) -> bool:
    # IMPORTANT: only the dataset's ingredients field can satisfy an ingredient.
    # Recipe titles, descriptions and tags are not proof that an ingredient is present.
    ingredient_items = [str(item).lower() for item in candidate.ingredients]
    aliases = INGREDIENT_ALIASES.get(canonical, [canonical])
    for item in ingredient_items:
        # Processed products containing an ingredient word are not always a
        # practical substitute for the ingredient the user says they have.
        if canonical == "egg" and any(_contains(item, x) for x in ("egg noodle", "egg noodles", "egg pasta", "egg roll wrapper", "egg substitute", "egg replacer")):
            continue
        if canonical == "chicken" and any(_contains(item, x) for x in ("chicken stock", "chicken broth", "chicken bouillon", "chicken flavour", "chicken flavor", "chicken seasoning")):
            continue
        if canonical == "beef" and any(_contains(item, x) for x in ("beef stock", "beef broth", "beef bouillon", "beef flavour", "beef flavor")):
            continue
        if canonical == "fish" and any(_contains(item, x) for x in ("fish sauce", "fish stock", "fish broth")):
            continue
        if any(_contains(item, alias) for alias in aliases):
            return True
    return False


def ingredient_match_lists(candidate: RecipeCandidate, requirements: ParsedRequirements) -> Tuple[List[str], List[str]]:
    found, absent = [], []
    for ingredient in requirements.required_ingredients:
        (found if _ingredient_match(candidate, ingredient) else absent).append(ingredient)
    return found, absent


def _diet_violations(candidate: RecipeCandidate, requirements: ParsedRequirements) -> List[str]:
    text = " ; ".join(candidate.ingredients).lower()
    violations = []
    if "vegan" in requirements.dietary_preferences:
        if any(_contains(text, x) for x in (*MEAT_TERMS, "egg", "eggs", *DAIRY_TERMS, "honey")):
            violations.append("Potential animal-derived ingredient conflicts with vegan preference")
    elif "vegetarian" in requirements.dietary_preferences:
        if any(_contains(text, x) for x in MEAT_TERMS):
            violations.append("Potential meat or seafood ingredient conflicts with vegetarian preference")
    if "dairy-free" in requirements.dietary_preferences and any(_contains(text, x) for x in DAIRY_TERMS):
        violations.append("Potential dairy ingredient conflicts with dairy-free preference")
    if "gluten-free" in requirements.dietary_preferences and any(_contains(text, x) for x in GLUTEN_TERMS):
        violations.append("Potential gluten ingredient conflicts with gluten-free preference")
    return violations


def filter_candidates_by_constraints(candidates: Sequence[RecipeCandidate], requirements: ParsedRequirements):
    """Return (accepted, rejected[(candidate, reasons)]). Hard requirements never become bonuses."""
    accepted, rejected = [], []
    for candidate in candidates:
        reasons = []
        _, missing = ingredient_match_lists(candidate, requirements)
        if missing:
            reasons.append("Missing required ingredients: " + ", ".join(missing))
        reasons.extend(_diet_violations(candidate, requirements))
        if requirements.max_cooking_minutes is not None and candidate.minutes > 0 and candidate.minutes > requirements.max_cooking_minutes:
            reasons.append(f"Cooking time {candidate.minutes} min exceeds limit {requirements.max_cooking_minutes} min")
        if reasons:
            rejected.append((candidate, reasons))
        else:
            accepted.append(candidate)
    return accepted, rejected


def filter_candidates_by_required_ingredients(candidates: Sequence[RecipeCandidate], requirements: ParsedRequirements):
    """Ingredient-only gate retained for focused tests and compatibility callers."""
    if not requirements.required_ingredients:
        return list(candidates), []
    accepted, rejected = [], []
    for candidate in candidates:
        _, missing = ingredient_match_lists(candidate, requirements)
        if missing:
            rejected.append((candidate, missing))
        else:
            accepted.append(candidate)
    return accepted, rejected


def _relative(value, values, higher_is_better=True):
    usable = [float(v) for v in values if v is not None]
    if value is None or len(usable) < 2 or max(usable) == min(usable):
        return 0.5
    normalized = (float(value) - min(usable)) / (max(usable) - min(usable))
    return normalized if higher_is_better else 1.0 - normalized


def _is_healthy_request(query: str) -> bool:
    q = query.lower()
    return any(x in q for x in ("healthy", "healthier", "nutritious", "light meal", "low calorie", "balanced"))


def _is_easy_request(query: str, requirements: ParsedRequirements) -> bool:
    q = query.lower()
    return any(x in q for x in ("easy", "simple", "quick", "fast", "beginner", "easy to prepare")) or requirements.max_cooking_minutes is not None


def score_candidates(candidates: Sequence[RecipeCandidate], requirements: ParsedRequirements, user_query: str, limit: int = 5) -> List[RecipeCandidate]:
    """Score candidates on a documented 0–100 scale after hard constraint filtering.

    Proposed PRD weights: ingredient utilisation 30%, explicit constraint satisfaction
    30%, time 15%, missing ingredients 10%, dietary/health fit 10%, difficulty 5%.
    Baseline rank is used only as a stable tie-breaker, not silently replaced.
    """
    if not candidates:
        return []
    q = user_query.lower()
    health = _is_healthy_request(q)
    easy = _is_easy_request(q, requirements)
    calories = [c.calories for c in candidates]
    proteins = [c.protein for c in candidates]
    times = [c.minutes if c.minutes > 0 else None for c in candidates]
    ingredient_counts = [len(c.ingredients) if c.ingredients else None for c in candidates]
    scored = []
    for c in candidates:
        matched, missing = ingredient_match_lists(c, requirements)
        ingredient_util = 100.0 * len(matched) / len(requirements.required_ingredients) if requirements.required_ingredients else 100.0
        constraint_score = 100.0  # candidates violating known hard constraints were removed first
        if requirements.max_cooking_minutes is not None:
            time_score = max(0.0, min(100.0, 100.0 * (1.0 - (c.minutes / max(1, requirements.max_cooking_minutes)) * 0.65))) if c.minutes > 0 else 50.0
        elif easy:
            time_score = 100.0 * _relative(c.minutes if c.minutes > 0 else None, times, False)
        else:
            time_score = 70.0
        extras = [i for i in c.ingredients if i.strip().lower() not in PANTRY_STAPLES and not any(_contains(i, a) for key in matched for a in INGREDIENT_ALIASES.get(key, [key]))]
        missing_score = max(0.0, 100.0 - 8.0 * len(extras))
        if health and c.calories is not None:
            calorie_fit = 100.0 * _relative(c.calories, calories, False)
            protein_fit = 100.0 * _relative(c.protein, proteins, True) if c.protein is not None else 50.0
            diet_score = 0.6 * calorie_fit + 0.4 * protein_fit
        else:
            diet_score = 100.0
        if easy:
            mins = c.minutes if c.minutes > 0 else 45
            count = len(c.ingredients) if c.ingredients else 10
            difficulty_score = 100.0 if mins <= 30 and count <= 8 else 75.0 if mins <= 45 and count <= 12 else 45.0
        else:
            difficulty_score = 70.0
        breakdown = {
            "ingredient_utilisation": round(ingredient_util, 2),
            "constraint_satisfaction": round(constraint_score, 2),
            "cooking_time": round(time_score, 2),
            "missing_ingredients": round(missing_score, 2),
            "diet_compatibility": round(diet_score, 2),
            "difficulty": round(difficulty_score, 2),
        }
        score = sum(breakdown[k] * SCORING_WEIGHTS[k] for k in SCORING_WEIGHTS)
        reasons = []
        if requirements.required_ingredients:
            reasons.append(f"Uses all {len(matched)} requested ingredient(s)")
        if requirements.max_cooking_minutes is not None and c.minutes > 0:
            reasons.append(f"Within the {requirements.max_cooking_minutes}-minute limit")
        if health and c.protein is not None:
            reasons.append(f"Nutrition metadata: {c.calories if c.calories is not None else 'unknown'} kcal, {c.protein:g} g protein")
        if easy:
            reasons.append("Ease estimate based on dataset time and ingredient count")
        c.local_suitability_score = round(score, 2)
        c.local_score_breakdown = breakdown
        c.local_reasons = reasons or ["Ranked using baseline relevance and documented local scoring"]
        scored.append((score, c.baseline_rank or 999999, c))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [c for _, _, c in scored[:limit]]
