"""Streamlit presentation layer. Recommendation logic lives in backend.pipeline."""
from __future__ import annotations
import json
import re
import streamlit as st
from backend.pipeline import run_pipeline
from backend.input_processor import INGREDIENT_ALIASES
from backend.config import GEMINI_API_KEY
from backend.preference_ranker import ingredient_match_lists

st.set_page_config(page_title="SmartRecipe AI", page_icon="🍲", layout="wide")
st.title("🍲 SmartRecipe AI")
st.caption("Frozen baseline retrieval → hard constraint validation → transparent scoring → AI ranking → validated cooking guidance")

with st.form("recipe_search", clear_on_submit=False):
    query = st.text_area(
        "What would you like to cook?",
        placeholder="Example: I have chicken and a few eggs. I want something healthy and easy to prepare.",
        height=95,
    )
    submitted = st.form_submit_button("Find recipes", type="primary", use_container_width=True)


def _baseline_trace(candidate, requirements):
    """Display source fields only, keeping the baseline snapshot distinct from enhancements."""
    matched, missing = ingredient_match_lists(candidate, requirements)
    return {
        "baseline_rank": candidate.baseline_rank,
        "recipe_id": candidate.recipe_id,
        "name": candidate.name,
        "baseline_similarity_score": candidate.baseline_similarity_score,
        "ingredients_from_dataset": candidate.ingredients,
        "required_ingredients_found": matched,
        "required_ingredients_missing": missing,
        "minutes_from_dataset": candidate.minutes,
        "calories_from_dataset": candidate.calories,
        "protein_g_from_dataset": candidate.protein,
    }


def _candidate_trace(candidate, requirements):
    return {
        **_baseline_trace(candidate, requirements),
        "local_suitability_score": candidate.local_suitability_score,
        "local_score_breakdown": candidate.local_score_breakdown,
        "local_reasons": candidate.local_reasons,
    }


def _render_recipe(position, recipe, requirements, extra, evaluation):
    with st.container(border=True):
        st.markdown(f"### {position}. {recipe.name}")
        metadata = [f"Local suitability: {recipe.local_suitability_score:.1f}/100"] if recipe.local_suitability_score is not None else []
        if evaluation:
            metadata.append(f"AI suitability: {evaluation.overall_score:.0f}/100")
        if recipe.minutes and recipe.minutes > 0:
            metadata.append(f"⏱️ {recipe.minutes} min total")
        if recipe.average_rating is not None:
            metadata.append(f"⭐ {recipe.average_rating:.1f} rating")
        if recipe.calories is not None:
            metadata.append(f"{recipe.calories:.0f} kcal")
        if recipe.protein is not None:
            metadata.append(f"{recipe.protein:.1f} g protein")
        if extra:
            metadata.append(f"Difficulty: {extra.difficulty_estimate.lower()} (AI estimate)")
        if metadata:
            st.caption("  ·  ".join(metadata))
        if extra and extra.short_description:
            st.write(extra.short_description)
        elif recipe.description and recipe.description != "No description provided.":
            st.write(recipe.description)
        if evaluation and evaluation.reason:
            st.write("**Why it matches:** " + evaluation.reason)
        elif recipe.local_reasons:
            st.write("**Why it matches:** " + "; ".join(recipe.local_reasons))

        matched, missing = ingredient_match_lists(recipe, requirements)
        if requirements.required_ingredients:
            st.markdown("**Required ingredients verified**")
            st.write(", ".join(matched))
            if missing:
                st.error("Final validation failed. This recipe must not be treated as a recommendation.")
        if recipe.ingredients:
            st.markdown("**Recipe ingredients from dataset**")
            st.write(", ".join(recipe.ingredients))
            requested_aliases = [alias for canonical in matched for alias in INGREDIENT_ALIASES.get(canonical, [canonical])]
            other_ingredients = [item for item in recipe.ingredients if not any(re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", item.lower()) for alias in requested_aliases)]
            pantry_staples = {"salt", "pepper", "black pepper", "water", "olive oil", "vegetable oil", "oil", "cooking oil"}
            pantry_items = [item for item in other_ingredients if item.strip().lower() in pantry_staples]
            other_ingredients = [item for item in other_ingredients if item not in pantry_items]
            if pantry_items:
                st.markdown("**Pantry staples**")
                st.write(", ".join(pantry_items))
            if other_ingredients:
                st.markdown("**Other ingredients you may need**")
                st.write(", ".join(other_ingredients))
        if extra:
            if extra.additional_ingredients:
                st.markdown("**Optional additions suggested by AI**")
                st.write(", ".join(extra.additional_ingredients))
            st.markdown("**How to make it (AI suggested guidance)**")
            for step_number, step in enumerate(extra.cooking_steps, start=1):
                st.markdown(f"{step_number}. {step}")
            if extra.practical_tip:
                st.markdown("**Tip:** " + extra.practical_tip)
            for warning in extra.warnings:
                st.warning(warning)


if submitted:
    query = query.strip()
    if len(query) < 3:
        st.warning("Please enter a few words about the ingredients or meal you want.")
    else:
        try:
            result = run_pipeline(query)
            req = result.requirements
            if not result.final_candidates and req.required_ingredients:
                st.warning("No recipe in the baseline retrieval pool satisfied every requested ingredient and other detected hard constraint. No mismatched recipe is being recommended. Inspect the rejected candidates below or try a broader request.")
            elif not result.final_candidates:
                st.info("No recipes satisfied the detected constraints. Try a broader request.")
            else:
                st.subheader("Your recipes")
                st.caption("Every displayed recipe passed the final hard constraint gate. AI instructions and difficulty are suggestions, not verified source instructions.")
                ai_evaluations = {e.recipe_id: e for e in result.ranking_response.candidate_evaluations} if result.ranking_response else {}
                for position, recipe in enumerate(result.final_candidates, start=1):
                    _render_recipe(position, recipe, req, result.enrichments.get(recipe.recipe_id), ai_evaluations.get(recipe.recipe_id))

            if result.ai_errors:
                st.info("Some AI features were unavailable for this request. Your eligible locally-ranked recipes remain available where possible.")

            # Detailed trace is persisted by backend.pipeline_trace, not exposed in the user interface.
            st.caption("Cooking time, rating and nutrition are dataset values when available. AI cooking steps and difficulty are suggestions, not verified original instructions.")
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            if GEMINI_API_KEY:
                message = message.replace(GEMINI_API_KEY, "[REDACTED]")
            st.error("We could not prepare your recipe list. Please try again.")
            # Exception detail is intentionally kept out of the user-facing interface.

st.divider()
st.caption("SmartRecipe AI preserves baseline retrieval, enforces ingredient constraints, scores locally, validates AI output, and records the stages for reproducible assessment evidence.")
