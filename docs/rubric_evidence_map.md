# Assessment evidence map

This map follows the SmartRecipe AI project requirements document. Check it against the exact current rubric published by the subject coordinator before submission because subject rubrics and weightings can differ.

| Requirement area | Evidence in this project | What to show the lecturer |
|---|---|---|
| 1. Industry problem, creative solution and AI workflow | `README.md`, `docs/architecture.md`, `streamlit_app.py` | Explain why recipe recommendation needs constraint-aware personalisation; demonstrate request → baseline → enhancement → final output |
| 2. At least three approaches and systematic testing | `run_experiments.py`, `data/assessment_test_cases.json`, `docs/evaluation_protocol.md`, generated `outputs/experiment_results_*.csv` | Run the same test set across A/B/C/D; report actual measured metrics, failures and limitations |
| 3. Reproducibility and technical documentation | `README.md`, `docs/reproducibility.md`, `docs/prompt_registry.md`, `.env.example` | Show setup, models/artifacts, prompt versions, scoring weights, commands and configuration |
| 4. Ethics and deployed-interface plausibility | `docs/ethics_and_risk.md`, app warnings, `.gitignore` | Discuss privacy/external processing and incorrect/allergy-sensitive recommendations with concrete lifecycle controls |
| 5. Critical reflection | `docs/reflection_template.md` | Complete using your actual development experience and experiment results; do not submit unedited placeholders |
| 6. Professional demonstration and communication | `docs/assessment_demo_script.md`, live Streamlit trace, experiment outputs | Demonstrate a real query, raw baseline output, rejected candidates, score breakdown, AI response, validation and results |

## Before submission checklist

- [ ] The original baseline app and model artifacts still exist and run.
- [ ] Run the complete unit test suite and retain the actual output.
- [ ] Run all five test cases in deterministic mode.
- [ ] If AI ranking is claimed as evaluated, run the AI experiment with a valid key and retain actual outputs.
- [ ] Complete human relevance and usefulness ratings with a real evaluator.
- [ ] Record any failures, skipped variants, or limitations.
- [ ] Verify citations and attribution for the source repository and all external materials.
- [ ] Replace the reflection template with your own truthful reflection.
- [ ] Compare this evidence map to the official rubric and check every line item.
