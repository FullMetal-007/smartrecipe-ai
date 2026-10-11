"""Manual Gemini experiment runner. Requires a valid GEMINI_API_KEY in .env.
This script records actual API results; it never substitutes a local heuristic.
"""
import json
import time
from pathlib import Path
from backend.baseline_service import baseline_service
from backend.ai_ranker import ai_ranker
from backend.constraint_validator import constraint_validator
from backend.input_processor import parse_requirements
from backend.config import GEMINI_API_KEY, GEMINI_MODEL, PROMPT_VERSION, CONFIG_VERSION
from backend.schemas import ExperimentRecord
from backend.experiment_logger import log_experiment

TEST_QUERIES = [
    "I have chicken, rice, spinach and tomato. I want a quick dinner.",
    "I want a vegetarian pasta recipe with tomato and cheese.",
    "I want a healthy Asian style meal using vegetables and rice.",
]

def run_experiment():
    if not GEMINI_API_KEY:
        raise SystemExit("No Gemini API key found. Set GEMINI_API_KEY in .env. No local fallback is used.")
    baseline_service.load_models()
    results=[]
    for index, query in enumerate(TEST_QUERIES, 1):
        start=time.perf_counter()
        retrieval_start=time.perf_counter()
        candidates=baseline_service.get_candidates(query, num_candidates=5)
        retrieval_latency=round(time.perf_counter()-retrieval_start, 3)
        ranking, provider, ai_latency, cache_hit=ai_ranker.rank_candidates(query, candidates)
        requirements=parse_requirements(query)
        validation=constraint_validator.validate(ranking,candidates,requirements)
        selected=next(c for c in candidates if c.recipe_id==ranking.selected_recipe_id)
        record=ExperimentRecord(
            user_query=query, parsed_requirements=requirements.model_dump(),
            candidate_names=[c.name for c in candidates], baseline_top_pick=candidates[0].name,
            baseline_retrieval_latency_s=retrieval_latency, ai_provider=provider, ai_model=GEMINI_MODEL,
            prompt_version=PROMPT_VERSION, config_version=CONFIG_VERSION,
            ai_selected_recipe=selected.name, ai_scores=[e.model_dump() for e in ranking.candidate_evaluations],
            final_reason=ranking.final_reason, validation_result=validation.model_dump(),
            api_calls=0 if cache_hit else 1, ai_latency_s=ai_latency,
            total_latency_s=round(time.perf_counter()-start,3), cache_hit=cache_hit,
            final_recommendation=selected.name, selection_changed_from_baseline=(selected.name != candidates[0].name)
        )
        log_experiment(record)
        result={"test_id":index,"query":query,"provider":provider,"model":GEMINI_MODEL,"baseline_top":candidates[0].name,"gemini_selection":selected.name,"changed":selected.name != candidates[0].name,"validation":validation.model_dump(),"cache_hit":cache_hit,"api_calls":record.api_calls,"latency_s":ai_latency}
        results.append(result)
        print(json.dumps(result,indent=2,ensure_ascii=False))
    output=Path("logs/gemini_experiment_v1.json")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"Actual Gemini experiment results saved to {output.resolve()}")
    return results

if __name__ == "__main__":
    run_experiment()
