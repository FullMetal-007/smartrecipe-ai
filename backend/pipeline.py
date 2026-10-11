"""Backend source of truth for the SmartRecipe AI recommendation workflow.

The Streamlit UI calls `run_pipeline` and renders the returned structured stages.
No recommendation, ranking, validation, or AI business logic belongs in the UI.
"""
from __future__ import annotations
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from backend.baseline_service import baseline_service
from backend.ai_ranker import ai_ranker
from backend.input_processor import parse_requirements
from backend.config import (
    GEMINI_API_KEY, GEMINI_MODEL, LLM_PROVIDER, NUM_CANDIDATES,
    NUM_RETRIEVAL_CANDIDATES, MAX_RETRIEVAL_CANDIDATES, MAX_CORRECTION_ATTEMPTS,
    PROMPT_VERSION, RANKING_PROMPT_VERSION, CONFIG_VERSION,
)
from backend.preference_ranker import score_candidates, ingredient_match_lists, filter_candidates_by_constraints
from backend.constraint_validator import constraint_validator
from backend.experiment_logger import log_experiment
from backend.pipeline_trace import write_pipeline_trace
from backend.schemas import ExperimentRecord, ParsedRequirements, RecipeCandidate, RecipeEnrichmentResponse, AIRankingResponse, ValidationResult

@dataclass
class PipelineResult:
    query: str
    requirements: ParsedRequirements
    baseline_candidates: List[RecipeCandidate]
    valid_candidates: List[RecipeCandidate]
    rejected_candidates: List[Tuple[RecipeCandidate, List[str]]]
    local_candidates: List[RecipeCandidate]
    final_candidates: List[RecipeCandidate]
    ranking_response: Optional[AIRankingResponse]
    validation_result: Optional[ValidationResult]
    enrichment_response: Optional[RecipeEnrichmentResponse]
    enrichments: Dict[str, Any]
    ai_errors: List[str]
    ai_request_preview: Dict[str, Any]
    metadata: Dict[str, Any]


def _safe_error(exc: Exception) -> str:
    message = f"{type(exc).__name__}: {exc}"
    if GEMINI_API_KEY:
        message = message.replace(GEMINI_API_KEY, "[REDACTED]")
    return message[:1200]


def _order_by_ai(local_candidates: List[RecipeCandidate], response: AIRankingResponse) -> List[RecipeCandidate]:
    scores = {e.recipe_id: e.overall_score for e in response.candidate_evaluations}
    selected_id = response.selected_recipe_id
    return sorted(local_candidates, key=lambda c: (c.recipe_id != selected_id, -scores.get(c.recipe_id, -1), c.baseline_rank))


def run_pipeline(query: str) -> PipelineResult:
    """Execute one request and return each real processing stage for display/evaluation."""
    query = query.strip()
    started = time.perf_counter()
    requirements = parse_requirements(query)
    requested_count = len(requirements.required_ingredients)
    retrieval_count = max(NUM_RETRIEVAL_CANDIDATES, 1000 if requested_count >= 2 else NUM_RETRIEVAL_CANDIDATES)
    retrieval_count = min(retrieval_count, MAX_RETRIEVAL_CANDIDATES)

    baseline_started = time.perf_counter()
    baseline_candidates = baseline_service.get_candidates(query, num_candidates=retrieval_count)
    baseline_latency = round(time.perf_counter() - baseline_started, 3)
    valid_candidates, rejected_candidates = filter_candidates_by_constraints(baseline_candidates, requirements)
    if len(valid_candidates) < min(NUM_CANDIDATES, 3) and retrieval_count < MAX_RETRIEVAL_CANDIDATES:
        expanded_started = time.perf_counter()
        retrieval_count = MAX_RETRIEVAL_CANDIDATES
        baseline_candidates = baseline_service.get_candidates(query, num_candidates=retrieval_count)
        baseline_latency += round(time.perf_counter() - expanded_started, 3)
        valid_candidates, rejected_candidates = filter_candidates_by_constraints(baseline_candidates, requirements)

    local_candidates = score_candidates(valid_candidates, requirements, query, limit=NUM_CANDIDATES)
    final_candidates = list(local_candidates)
    ranking_response = None
    validation_result = None
    enrichment_response = None
    enrichments: Dict[str, Any] = {}
    ai_errors: List[str] = []
    provider_name = "baseline + deterministic local enhancement"
    ranking_latency = enrichment_latency = 0.0
    ranking_cache_hit = enrichment_cache_hit = False
    rank_api_calls = enrichment_api_calls = 0
    correction_attempted = False

    ai_request_preview = {
        "user_request": query,
        "parsed_requirements": requirements.model_dump(),
        "candidate_recipes_sent_to_ai": [
            {"recipe_id": c.recipe_id, "name": c.name, "ingredients": c.ingredients[:22],
             "minutes": c.minutes if c.minutes > 0 else None,
             "local_suitability_score": c.local_suitability_score}
            for c in local_candidates
        ],
        "guardrails": [
            "Candidates were retrieved by the frozen baseline model.",
            "Only source ingredient lists satisfy required ingredient checks.",
            "AI cannot add a new recipe or change source ingredients, time, rating, or nutrition.",
            "AI output is checked against candidate identity and user constraints.",
        ],
    }

    if local_candidates and LLM_PROVIDER == "gemini" and GEMINI_API_KEY:
        try:
            ranking_response, provider_name, ranking_latency, ranking_cache_hit = ai_ranker.rank_candidates(query, local_candidates)
            rank_api_calls += 0 if ranking_cache_hit else 1
            validation_result = constraint_validator.validate(ranking_response, local_candidates, requirements)
            if not validation_result.valid and MAX_CORRECTION_ATTEMPTS > 0:
                correction_attempted = True
                correction_context = "Deterministic validation failures: " + "; ".join(validation_result.violations)
                ranking_response, provider_name, correction_latency, _ = ai_ranker.rank_candidates(query, local_candidates, correction_context=correction_context)
                ranking_latency += correction_latency
                rank_api_calls += 1
                validation_result = constraint_validator.validate(ranking_response, local_candidates, requirements)
            if validation_result.valid:
                final_candidates = _order_by_ai(local_candidates, ranking_response)
            else:
                ai_errors.append("AI ranking failed deterministic validation; final order remains the safe local ranking.")
        except Exception as exc:
            ai_errors.append("AI ranking: " + _safe_error(exc))
        try:
            enrichment_response, enrich_provider, enrichment_latency, enrichment_cache_hit = ai_ranker.enrich_candidates(query, final_candidates)
            provider_name = enrich_provider
            enrichment_api_calls += 0 if enrichment_cache_hit else 1
            enrichments = {item.recipe_id: item for item in enrichment_response.recipes}
        except Exception as exc:
            ai_errors.append("AI cooking guidance: " + _safe_error(exc))
    elif local_candidates:
        ai_errors.append("AI is not configured. Add GEMINI_API_KEY to the local .env file to enable AI ranking and cooking guidance.")

    # A second, post-AI safety gate is mandatory. AI output cannot relax constraints.
    final_valid, _ = filter_candidates_by_constraints(final_candidates, requirements)
    valid_ids = {c.recipe_id for c in final_valid}
    final_candidates = [c for c in final_candidates if c.recipe_id in valid_ids]
    final_ids = {c.recipe_id for c in final_candidates}
    enrichments = {rid: item for rid, item in enrichments.items() if rid in final_ids}

    total_latency = round(time.perf_counter() - started, 3)
    metadata = {
        "baseline_model": "Frozen TF-IDF query transform + saved combined embeddings + cosine similarity",
        "baseline_artifacts_modified": False,
        "retrieval_pool_size": retrieval_count,
        "display_limit": NUM_CANDIDATES,
        "ai_provider": provider_name,
        "ai_model": GEMINI_MODEL if ranking_response or enrichment_response else None,
        "ranking_prompt_version": RANKING_PROMPT_VERSION,
        "enrichment_prompt_version": PROMPT_VERSION,
        "config_version": CONFIG_VERSION,
        "ranking_cache_hit": ranking_cache_hit,
        "enrichment_cache_hit": enrichment_cache_hit,
        "ranking_latency_seconds": ranking_latency,
        "enrichment_latency_seconds": enrichment_latency,
        "ai_api_calls_this_request": rank_api_calls + enrichment_api_calls,
        "total_latency_seconds": total_latency,
        "candidate_count_before_gate": len(baseline_candidates),
        "candidate_count_after_gate": len(valid_candidates),
        "candidate_count_final": len(final_candidates),
        "correction_attempted": correction_attempted,
    }

    # Full diagnostic trace is written to a local backend JSONL file, never rendered in the user UI.
    trace_payload = {
        "query": query,
        "parsed_requirements": requirements.model_dump(),
        "baseline_candidates": [c.model_dump() | {"recipe_id": c.recipe_id} for c in baseline_candidates],
        "hard_gate": {
            "accepted": [c.model_dump() | {"recipe_id": c.recipe_id} for c in valid_candidates],
            "rejected": [{"candidate": c.model_dump() | {"recipe_id": c.recipe_id}, "reasons": reasons} for c, reasons in rejected_candidates],
        },
        "local_scoring": [c.model_dump() | {"recipe_id": c.recipe_id} for c in local_candidates],
        "ai_request_preview": ai_request_preview,
        "ai_ranking_output": ranking_response.model_dump() if ranking_response else None,
        "ai_validation": validation_result.model_dump() if validation_result else None,
        "ai_enrichment_output": enrichment_response.model_dump() if enrichment_response else None,
        "ai_errors": ai_errors,
        "final_candidates": [c.model_dump() | {"recipe_id": c.recipe_id} for c in final_candidates],
        "metadata": {**metadata, "baseline_retrieval_latency_seconds": baseline_latency},
    }
    try:
        trace_path = write_pipeline_trace(trace_payload)
        if trace_path:
            metadata["backend_trace_file"] = trace_path
    except OSError as trace_exc:
        # Logging failure must not interrupt a user's recipe request.
        metadata["backend_trace_write_error"] = type(trace_exc).__name__

    record = ExperimentRecord(
        user_query=query,
        parsed_requirements=requirements.model_dump(),
        candidate_names=[c.name for c in final_candidates],
        baseline_top_pick=baseline_candidates[0].name if baseline_candidates else "",
        baseline_retrieval_latency_s=baseline_latency,
        ai_provider=provider_name,
        ai_model=GEMINI_MODEL,
        prompt_version=f"rank:{RANKING_PROMPT_VERSION};enrich:{PROMPT_VERSION}",
        config_version=CONFIG_VERSION,
        ai_selected_recipe=ranking_response.selected_recipe if ranking_response and validation_result and validation_result.valid else "",
        ai_scores=[item.model_dump() for item in ranking_response.candidate_evaluations] if ranking_response else [],
        final_reason=(ranking_response.final_reason if ranking_response and validation_result and validation_result.valid else "Deterministic local scoring; AI ranking unavailable or rejected by validation."),
        validation_result={"valid": bool(final_candidates) and all(not ingredient_match_lists(c, requirements)[1] for c in final_candidates), "rejected_candidate_count": len(rejected_candidates), "ai_validation": validation_result.model_dump() if validation_result else None},
        correction_required=correction_attempted,
        correction_succeeded=bool(validation_result and validation_result.valid) if correction_attempted else None,
        api_calls=rank_api_calls + enrichment_api_calls,
        ai_latency_s=ranking_latency + enrichment_latency,
        total_latency_s=total_latency,
        cache_hit=ranking_cache_hit or enrichment_cache_hit,
        final_recommendation=", ".join(c.name for c in final_candidates),
        selection_changed_from_baseline=bool(final_candidates and baseline_candidates and final_candidates[0].name != baseline_candidates[0].name),
    )
    log_experiment(record)

    return PipelineResult(
        query=query, requirements=requirements, baseline_candidates=baseline_candidates,
        valid_candidates=valid_candidates, rejected_candidates=rejected_candidates,
        local_candidates=local_candidates, final_candidates=final_candidates,
        ranking_response=ranking_response, validation_result=validation_result,
        enrichment_response=enrichment_response, enrichments=enrichments,
        ai_errors=ai_errors, ai_request_preview=ai_request_preview,
        metadata={**metadata, "baseline_retrieval_latency_seconds": baseline_latency},
    )
