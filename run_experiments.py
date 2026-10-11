"""Run reproducible A/B/C/D experiments on the same assessment test cases.

By default, only baseline and deterministic constraint/scoring stages run. Pass
--include-ai to run the Gemini ranking variants; a valid local .env key is required.
All reported numbers are computed from this run. Human ratings are intentionally blank.
"""
from __future__ import annotations
import argparse, csv, json, time
from datetime import datetime
from pathlib import Path
from backend.baseline_service import baseline_service
from backend.input_processor import parse_requirements
from backend.preference_ranker import filter_candidates_by_constraints, score_candidates, ingredient_match_lists, _diet_violations
from backend.constraint_validator import constraint_validator
from backend.ai_ranker import ai_ranker
from backend.config import GEMINI_API_KEY, GEMINI_MODEL, NUM_RETRIEVAL_CANDIDATES, MAX_RETRIEVAL_CANDIDATES, RANKING_PROMPT_VERSION, PROMPT_VERSION, CONFIG_VERSION

ROOT = Path(__file__).resolve().parent
CASES_PATH = ROOT / "data" / "assessment_test_cases.json"
OUTPUT_DIR = ROOT / "outputs"

def metric_for(candidate, requirements):
    if candidate is None:
        return {"ingredient_utilisation_pct": 0.0 if requirements.required_ingredients else 100.0,
                "constraint_satisfaction_pct": 0.0, "time_compliance_pct": 0.0 if requirements.max_cooking_minutes else 100.0,
                "diet_compliance_pct": 0.0, "missing_required_ingredients_count": len(requirements.required_ingredients),
                "candidate_exists": 0, "hard_constraints_passed": 0}
    _, missing = ingredient_match_lists(candidate, requirements)
    time_ok = not requirements.max_cooking_minutes or candidate.minutes <= 0 or candidate.minutes <= requirements.max_cooking_minutes
    violations = _diet_violations(candidate, requirements)
    hard_ok = not missing and not violations and time_ok
    return {
        "ingredient_utilisation_pct": round(100 * (len(requirements.required_ingredients) - len(missing)) / len(requirements.required_ingredients), 2) if requirements.required_ingredients else 100.0,
        "constraint_satisfaction_pct": 100.0 if hard_ok else 0.0,
        "time_compliance_pct": 100.0 if time_ok else 0.0,
        "diet_compliance_pct": 0.0 if violations else 100.0,
        "missing_required_ingredients_count": len(missing),
        "candidate_exists": 1, "hard_constraints_passed": 1 if hard_ok else 0,
    }

def row(test, version, status, query, candidate, baseline_top, latency, api_calls=0, cache_hit=False, validation="", note=""):
    req = parse_requirements(query)
    metrics = metric_for(candidate, req)
    return {
        "test_id": test["test_id"], "version": version, "status": status,
        "user_request": query, "baseline_top_recipe": baseline_top,
        "recommended_recipe": candidate.name if candidate else "",
        **metrics, "human_relevance_rating_1_to_5": "", "human_usefulness_rating_1_to_5": "",
        "latency_seconds": round(latency, 3), "ai_api_calls": api_calls,
        "cache_hit": cache_hit, "validation": validation, "notes": note,
    }

def _is_quota_exhaustion(exc):
    """Return True for provider quota/rate-limit failures so we do not waste calls."""
    message = f"{type(exc).__name__}: {exc}".lower()
    return ("resource_exhausted" in message or "quota exceeded" in message
            or "429" in message or "rate limit" in message)

def run(include_ai=False, limit=None):
    if include_ai and not GEMINI_API_KEY:
        raise SystemExit("--include-ai requires GEMINI_API_KEY in the local .env file. No fake AI results are generated.")
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if limit:
        cases = cases[:limit]
    baseline_service.load_models()
    rows = []
    ai_quota_exhausted = False
    ai_quota_message = ""
    for test in cases:
        query = test["request"]
        req = parse_requirements(query)
        count = min(MAX_RETRIEVAL_CANDIDATES, max(NUM_RETRIEVAL_CANDIDATES, 1000 if len(req.required_ingredients) >= 2 else NUM_RETRIEVAL_CANDIDATES))
        start = time.perf_counter()
        baseline = baseline_service.get_candidates(query, num_candidates=count)
        retrieval_latency = time.perf_counter() - start
        valid, rejected = filter_candidates_by_constraints(baseline, req)
        if len(valid) < min(3, 5) and count < MAX_RETRIEVAL_CANDIDATES:
            start_expand = time.perf_counter()
            count = MAX_RETRIEVAL_CANDIDATES
            baseline = baseline_service.get_candidates(query, num_candidates=count)
            retrieval_latency += time.perf_counter() - start_expand
        baseline_top = baseline[0] if baseline else None
        rows.append(row(test, "A: Original baseline", "completed", query, baseline_top, baseline_top.name if baseline_top else "", retrieval_latency, note="Raw baseline only; retained for comparison, not a safe final recommendation."))

        if include_ai and baseline and not ai_quota_exhausted:
            t = time.perf_counter()
            try:
                ranking, provider, ai_latency, cache_hit = ai_ranker.rank_candidates(query, baseline[:5])
                chosen = next(c for c in baseline[:5] if c.recipe_id == ranking.selected_recipe_id)
                validation = constraint_validator.validate(ranking, baseline[:5], req)
                rows.append(row(test, "B: Baseline + AI ranking", "completed", query, chosen, baseline_top.name, time.perf_counter()-t,
                                api_calls=0 if cache_hit else 1, cache_hit=cache_hit, validation=json.dumps(validation.model_dump()),
                                note="AI ranking is evaluated without hard filtering so constraint failures remain measurable."))
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                rows.append(row(test, "B: Baseline + AI ranking", "failed", query, None, baseline_top.name, time.perf_counter()-t, api_calls=1, note=message))
                if _is_quota_exhaustion(exc):
                    ai_quota_exhausted = True
                    ai_quota_message = "Gemini quota/rate limit reached; further AI requests skipped for this run. " + message[:700]
        else:
            skip_note = (ai_quota_message or "Run with --include-ai and configure GEMINI_API_KEY.")
            rows.append(row(test, "B: Baseline + AI ranking", "skipped", query, None, baseline_top.name, 0, note=skip_note))

        valid, rejected = filter_candidates_by_constraints(baseline, req)
        local = score_candidates(valid, req, query, limit=5)
        if include_ai and local and not ai_quota_exhausted:
            t = time.perf_counter()
            try:
                ranking, provider, ai_latency, cache_hit = ai_ranker.rank_candidates(query, local)
                validation = constraint_validator.validate(ranking, local, req)
                chosen = next(c for c in local if c.recipe_id == ranking.selected_recipe_id)
                rows.append(row(test, "C: AI ranking + hard constraints + score", "completed", query, chosen, baseline_top.name, time.perf_counter()-t,
                                api_calls=0 if cache_hit else 1, cache_hit=cache_hit, validation=json.dumps(validation.model_dump()),
                                note=f"Accepted {len(valid)} and rejected {len(rejected)} baseline candidates before AI ranking."))
                # D uses same constrained candidate set. It performs a correction only if validation fails.
                t = time.perf_counter()
                d_rank = ranking; d_validation = validation; d_calls = 0; d_cache = True
                correction_note = "Reused Version C's ranking response; no additional request required."
                if not validation.valid:
                    d_rank, _, correction_latency, _ = ai_ranker.rank_candidates(query, local, correction_context="Deterministic validation failures: " + "; ".join(validation.violations))
                    d_calls += 1
                    d_validation = constraint_validator.validate(d_rank, local, req)
                    correction_note = f"One correction attempted; success={d_validation.valid}."
                d_chosen = next((c for c in local if c.recipe_id == d_rank.selected_recipe_id), None)
                rows.append(row(test, "D: AI ranking + validation + revision", "completed", query, d_chosen, baseline_top.name, time.perf_counter()-t,
                                api_calls=d_calls, cache_hit=d_cache, validation=json.dumps(d_validation.model_dump()), note=correction_note))
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                rows.append(row(test, "C: AI ranking + hard constraints + score", "failed", query, local[0] if local else None, baseline_top.name, time.perf_counter()-t, api_calls=1, note=message))
                rows.append(row(test, "D: AI ranking + validation + revision", "failed", query, local[0] if local else None, baseline_top.name, 0, note="Initial constrained AI ranking failed; see C row."))
                if _is_quota_exhaustion(exc):
                    ai_quota_exhausted = True
                    ai_quota_message = "Gemini quota/rate limit reached; further AI requests skipped for this run. " + message[:700]
        else:
            # Keep the deterministic constrained scorer measurable even if AI is disabled or quota-exhausted.
            c_note = f"Accepted {len(valid)} and rejected {len(rejected)} candidates. AI ranking was not run."
            if ai_quota_exhausted:
                c_note += " " + ai_quota_message
            rows.append(row(test, "C: Hard constraints + local score (AI skipped)", "completed", query, local[0] if local else None, baseline_top.name, 0,
                            note=c_note))
            d_note = ai_quota_message or "Run with --include-ai and configure GEMINI_API_KEY."
            rows.append(row(test, "D: AI ranking + validation + revision", "skipped", query, None, baseline_top.name, 0,
                            note=d_note))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = OUTPUT_DIR / f"experiment_results_{stamp}.csv"
    json_path = OUTPUT_DIR / f"experiment_results_{stamp}.json"
    if rows:
        with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader(); writer.writerows(rows)
    metadata = {"run_timestamp": datetime.now().isoformat(), "include_ai": include_ai,
                "ai_model": GEMINI_MODEL if include_ai else None, "ranking_prompt_version": RANKING_PROMPT_VERSION,
                "enrichment_prompt_version": PROMPT_VERSION, "config_version": CONFIG_VERSION,
                "test_cases_file": str(CASES_PATH.relative_to(ROOT)), "results_csv": str(csv_path.relative_to(ROOT)),
                "results": rows, "human_ratings": "Blank by design until a human evaluator supplies ratings."}
    json_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = []
    for version in dict.fromkeys(r["version"] for r in rows):
        subset = [r for r in rows if r["version"] == version and r["status"] == "completed"]
        if not subset:
            summary.append({"version": version, "completed_cases": 0, "note": "No completed rows; inspect per-case results."})
            continue
        def mean(key):
            vals = [float(r[key]) for r in subset if r.get(key) not in (None, "")]
            return round(sum(vals) / len(vals), 2) if vals else None
        summary.append({"version": version, "completed_cases": len(subset), "total_cases": len([r for r in rows if r["version"] == version]),
                        "mean_ingredient_utilisation_pct": mean("ingredient_utilisation_pct"),
                        "mean_constraint_satisfaction_pct": mean("constraint_satisfaction_pct"),
                        "mean_time_compliance_pct": mean("time_compliance_pct"),
                        "mean_diet_compliance_pct": mean("diet_compliance_pct"),
                        "mean_missing_required_ingredients": mean("missing_required_ingredients_count"),
                        "mean_latency_seconds": mean("latency_seconds"),
                        "mean_ai_api_calls": mean("ai_api_calls"),
                        "human_ratings_collected": False})
    summary_path = OUTPUT_DIR / f"experiment_summary_{stamp}.json"
    summary_path.write_text(json.dumps({"run_timestamp": datetime.now().isoformat(), "summary_is_computed_from_this_run": True, "versions": summary}, indent=2), encoding="utf-8")
    metadata["summary_json"] = str(summary_path.relative_to(ROOT))
    json_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved actual experiment data to:\n  {csv_path}\n  {json_path}\n  {summary_path}")
    if ai_quota_exhausted:
        print("Gemini quota/rate limit detected. Remaining AI calls were skipped; deterministic baseline/local scoring continued.")
    print("Human rating fields are blank; do not claim model superiority until results and human review are analysed.")
    return rows

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-ai", action="store_true", help="Run real Gemini ranking variants; requires a valid .env key and incurs API usage.")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of test cases for a quick trial.")
    args = parser.parse_args()
    run(include_ai=args.include_ai, limit=args.limit)
