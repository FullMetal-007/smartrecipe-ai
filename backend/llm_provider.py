"""Provider interface and strict Gemini API implementation."""
from __future__ import annotations
import json, time
from abc import ABC, abstractmethod
from typing import List, Tuple
from backend.config import GEMINI_API_KEY, GEMINI_MODEL, AI_TEMPERATURE, PROMPTS_DIR, PROMPT_VERSION, RANKING_PROMPT_VERSION
from backend.schemas import AIRankingResponse, RecipeCandidate, RecipeEnrichmentResponse

class LLMProvider(ABC):
    provider_name = "abstract"
    model_name = "unknown"
    prompt_version = PROMPT_VERSION
    @abstractmethod
    def rank_candidates(self, user_query: str, candidates: List[RecipeCandidate], correction_context: str = "") -> Tuple[AIRankingResponse, float]: ...

class GeminiProvider(LLMProvider):
    provider_name = "gemini"
    def __init__(self):
        if not GEMINI_API_KEY:
            raise RuntimeError("Gemini API key missing. Add GEMINI_API_KEY to the project .env file.")
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError("google-genai is not installed. Run pip install -r requirements.txt.") from exc
        self._genai_types = None
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_name = GEMINI_MODEL
        ranking_prompt_file = PROMPTS_DIR / f"ai_ranking_{RANKING_PROMPT_VERSION}.txt"
        self.system_prompt = ranking_prompt_file.read_text(encoding="utf-8") if ranking_prompt_file.exists() else "Rank only the supplied candidates. Never invent recipes. Return valid JSON matching the schema."
        enrichment_prompt_file = PROMPTS_DIR / f"enrichment_{PROMPT_VERSION}.txt"
        self.enrichment_prompt = enrichment_prompt_file.read_text(encoding="utf-8") if enrichment_prompt_file.exists() else "Write concise cooking cards for the supplied recipes, preserving exact IDs, names and order. Return JSON only."
        correction_file = PROMPTS_DIR / f"correction_{RANKING_PROMPT_VERSION}.txt"
        self.correction_prompt = correction_file.read_text(encoding="utf-8") if correction_file.exists() else ""

    def rank_candidates(self, user_query: str, candidates: List[RecipeCandidate], correction_context: str = "") -> Tuple[AIRankingResponse, float]:
        from backend.input_processor import parse_requirements
        requirements = parse_requirements(user_query)
        payload = {
            "user_request": user_query,
            "parsed_requirements": requirements.model_dump(),
            "correction_context": correction_context,
            "rule": "Select exactly one candidate from this list. Do not create or rename recipes. Scores must be 0 to 100. Use only supplied facts. Consider the local score as transparent heuristic evidence, not ground truth.",
            "candidates": [{"recipe_id": c.recipe_id, "name": c.name, "minutes": c.minutes, "ingredients": c.ingredients[:30], "tags": c.tags[:20], "description": c.description[:400], "baseline_rank": c.baseline_rank, "baseline_similarity": c.baseline_similarity_score, "local_suitability_score": c.local_suitability_score, "local_score_breakdown": c.local_score_breakdown, "local_reasons": c.local_reasons, "protein": c.protein, "calories": c.calories} for c in candidates],
            "required_response_fields": AIRankingResponse.model_json_schema(),
            "scoring_criteria": {"ingredient_compatibility": 30, "intent_compatibility": 30, "constraint_satisfaction": 30, "practical_suitability": 10}
        }
        prompt = self.system_prompt
        if correction_context:
            prompt += "\n\n" + self.correction_prompt
        start=time.perf_counter()
        from google.genai import types
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=json.dumps(payload, ensure_ascii=False),
            config=types.GenerateContentConfig(
                temperature=AI_TEMPERATURE,
                response_mime_type="application/json",
                response_schema=AIRankingResponse,
                system_instruction=prompt,
            ),
        )
        latency=round(time.perf_counter()-start, 3)
        if not response.text:
            raise ValueError("Gemini returned an empty response.")
        parsed=AIRankingResponse.model_validate_json(response.text)
        candidate_by_id={c.recipe_id:c for c in candidates}
        if parsed.selected_recipe_id not in candidate_by_id:
            raise ValueError("Gemini selected a recipe outside the baseline candidate list.")
        if len(parsed.candidate_evaluations) != len(candidates):
            raise ValueError("Gemini did not evaluate exactly the supplied candidates.")
        for evaluation in parsed.candidate_evaluations:
            candidate=candidate_by_id.get(evaluation.recipe_id)
            if candidate is None or evaluation.recipe_name != candidate.name:
                raise ValueError("Gemini returned an unknown candidate or mismatched recipe identity.")
        return parsed, latency


    def enrich_candidates(self, user_query: str, candidates: List[RecipeCandidate]) -> Tuple[RecipeEnrichmentResponse, float]:
        """Generate concise recipe cards for all five selected recipes in one API call."""
        from backend.input_processor import parse_requirements

        requirements = parse_requirements(user_query)
        payload = {
            "intent": {
                "ingredients": requirements.required_ingredients,
                "preferences": [
                    name for name, active in (
                        ("healthy", any(x in user_query.lower() for x in ("healthy", "healthier", "nutritious", "light meal"))),
                        ("easy", any(x in user_query.lower() for x in ("easy", "simple", "quick", "fast"))),
                    ) if active
                ],
            },
            "recipes": [
                {
                    "id": c.recipe_id,
                    "name": c.name,
                    "ingredients": c.ingredients[:22],
                    "minutes": c.minutes if c.minutes > 0 else None,
                }
                for c in candidates
            ],
        }
        prompt = self.enrichment_prompt
        start = time.perf_counter()
        from google.genai import types
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=RecipeEnrichmentResponse,
                system_instruction=prompt,
            ),
        )
        latency = round(time.perf_counter() - start, 3)
        if not response.text:
            raise ValueError("Gemini returned an empty recipe enrichment response.")
        parsed = RecipeEnrichmentResponse.model_validate_json(response.text)
        if len(parsed.recipes) != len(candidates):
            raise ValueError("Gemini must return exactly one recipe card for every selected recipe.")
        for enrichment, candidate in zip(parsed.recipes, candidates):
            if enrichment.recipe_id != candidate.recipe_id or enrichment.recipe_name != candidate.name:
                raise ValueError("Gemini changed a recipe identity or order.")
            if not 3 <= len(enrichment.cooking_steps) <= 4:
                raise ValueError("Each recipe card must contain three or four suggested cooking steps.")
            if enrichment.difficulty_estimate not in {"Easy", "Moderate", "Challenging", "Unknown"}:
                raise ValueError("Gemini returned an invalid difficulty estimate.")
        return parsed, latency
