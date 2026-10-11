# Evaluation protocol

## Research question

Does adding transparent constraint validation, local suitability scoring, and an optional generative ranking layer improve the relevance and constraint compliance of candidates retrieved by the existing recipe recommender?

## Experimental versions

| Version | Workflow | Purpose |
|---|---|---|
| A | Original baseline retrieval, no enhancement | Reference output; not assumed safe for final user-facing recommendations |
| B | Baseline top candidates + Gemini ranking | Measures AI ranking without hard pre-filtering; constraint violations remain measurable |
| C | Baseline candidate pool + hard constraints + local score + Gemini ranking | Measures the effect of filtering and transparent scoring before AI ranking |
| D | Version C + deterministic post-validation + one correction attempt if validation fails | Measures whether validation and limited revision reduce invalid selections |

The app's normal recommendation path always applies hard constraints regardless of experimental mode. Version A/B are comparison outputs only in the experiment runner, not safe production recommendations.

## Fixed test set

`data/assessment_test_cases.json` contains five realistic requests. The exact same cases are replayed across variants. T01 tests the user's motivating chicken and egg scenario. T05 is a deliberate conflict case: chicken and rice are required while the user requests a vegan meal. The expected system behavior is to report no valid match, not silently ignore the conflict.

## Metrics

- **Ingredient utilisation (%)** = required ingredients present in the selected recipe's dataset ingredient list / number of required ingredients × 100. If no ingredients are requested, record 100% as not applicable and explain this convention.
- **Constraint satisfaction (%)** = 100 if the selected recipe satisfies all detected required ingredients, explicit time limit when known, and detectable diet constraints; otherwise 0. This strict metric is intentionally conservative.
- **Cooking time compliance (%)** = 100 if the known dataset time is within the explicit limit or no time limit is requested; otherwise 0. Unknown dataset time is recorded as unverifiable in notes.
- **Missing required ingredient count** = number of requested ingredients absent from the selected recipe's source ingredient list.
- **Human relevance / usefulness** = human ratings from 1 to 5 using the blank columns in the generated CSV. Do not fabricate these values.
- **Latency and API calls** = measured during the run; cache hits are distinguished from new API calls.

## Scoring configuration

Initial proposed weights from the PRD are used: ingredient utilisation 30%, constraint satisfaction 30%, cooking time 15%, missing ingredients 10%, dietary/health fit 10%, and difficulty 5%. Candidates that fail hard ingredient, detectable dietary, or known time constraints are removed before local scoring. The local score is a transparent ranking aid, not proof of real-world recipe quality. Weights should be treated as an initial experimental configuration and changed only with a documented rationale.

## Reproduction

From the project root, install requirements and configure `.env`. Run deterministic baseline/constraint tests with:

```powershell
python -m pytest -q
python run_experiments.py
```

To run the real Gemini ranking variants and incur API usage:

```powershell
python run_experiments.py --include-ai
```

Use `--limit 1` for a small smoke run. Outputs are timestamped under `outputs/`. Each run contains actual output from the current local model/API configuration. The script intentionally leaves human ratings blank. Compare the versions using the generated CSV, then discuss cases where performance did not improve as well as cases where it did.

## Reporting rules

- Never report an improvement percentage until it has been computed from a completed run.
- State the Python version, package versions, model ID, prompt versions, cache status, test cases, and date of the run.
- Do not compare results from different test sets as if they were controlled.
- Record missing datasets, API failures, skipped variants, and unavailable nutrition metadata as limitations rather than filling gaps with assumptions.
