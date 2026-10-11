"""Cached Gemini ranking and recipe-card enrichment orchestration. No silent AI substitution."""
import hashlib, json, time
from pathlib import Path
from typing import List, Tuple
from backend.config import AI_CACHE_ENABLED, CACHE_DIR, CONFIG_VERSION, LLM_PROVIDER, PROMPT_VERSION, RANKING_PROMPT_VERSION
from backend.schemas import AIRankingResponse, RecipeCandidate, RecipeEnrichmentResponse
from backend.llm_provider import GeminiProvider

class AIRanker:
    def __init__(self): self._provider=None
    def _get_provider(self):
        if LLM_PROVIDER != "gemini":
            raise RuntimeError("LLM_PROVIDER must be 'gemini' for the assessment experiment. No silent local fallback is enabled.")
        if self._provider is None: self._provider=GeminiProvider()
        return self._provider
    def _cache_path(self, query: str, candidates: List[RecipeCandidate]) -> Path:
        provider=self._get_provider()
        body={"query":query,"candidate_ids":[c.recipe_id for c in candidates],"model":provider.model_name,"prompt":RANKING_PROMPT_VERSION,"config":CONFIG_VERSION}
        key=hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest()
        CACHE_DIR.mkdir(parents=True,exist_ok=True)
        return CACHE_DIR / f"{key}.json"
    def rank_candidates(self, user_query: str, candidates: List[RecipeCandidate], correction_context: str = "") -> Tuple[AIRankingResponse, str, float, bool]:
        if not candidates: raise ValueError("Baseline returned no candidates.")
        provider=self._get_provider()
        # Correction responses must never reuse a ranking cache entry.
        cache_path=self._cache_path(user_query,candidates) if not correction_context else None
        if AI_CACHE_ENABLED and cache_path and cache_path.exists():
            return AIRankingResponse.model_validate_json(cache_path.read_text(encoding="utf-8")), provider.provider_name, 0.0, True
        result, latency=provider.rank_candidates(user_query,candidates,correction_context)
        if AI_CACHE_ENABLED and cache_path:
            cache_path.write_text(result.model_dump_json(indent=2),encoding="utf-8")
        return result, provider.provider_name, latency, False
    def enrich_candidates(self, user_query: str, candidates: List[RecipeCandidate]) -> Tuple[RecipeEnrichmentResponse, str, float, bool]:
        """One cached Gemini request enriches the final candidate list without changing recipe identity."""
        if not candidates:
            raise ValueError("Baseline returned no candidates.")
        provider = self._get_provider()
        body = {"mode": "enrichment", "query": user_query, "candidate_ids": [c.recipe_id for c in candidates],
                "model": provider.model_name, "prompt": PROMPT_VERSION, "config": CONFIG_VERSION}
        key = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path = CACHE_DIR / f"enrichment_{key}.json"
        if AI_CACHE_ENABLED and cache_path.exists():
            return RecipeEnrichmentResponse.model_validate_json(cache_path.read_text(encoding="utf-8")), provider.provider_name, 0.0, True
        result, latency = provider.enrich_candidates(user_query, candidates)
        if AI_CACHE_ENABLED:
            cache_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        return result, provider.provider_name, latency, False


ai_ranker=AIRanker()
