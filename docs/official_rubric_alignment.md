# Official Assessment 3 Rubric Alignment

This map is based on the supplied La Trobe University rubric for “Assessment 3: Creative application of AI for industry (video presentation)”. The rubric weights are Criterion 1 = 30%, Criterion 2 = 25%, Criterion 3 = 5%, Criterion 4 = 15%, Criterion 5 = 15%, Criterion 6 = 10%.

## Criterion 1: Project idea, implementation and creativity (30%)
Evidence: README, architecture diagrams, baseline workflow, enhanced pipeline, working Streamlit prototype and live trace. Demonstrate natural-language input transformation, original baseline retrieval, constraint checks, scoring, optional Gemini ranking/enrichment, validation and final output. Do not claim the live AI stages work until a real API call succeeds.

## Criterion 2: Exploration and experimentation (25%)
Evidence: `run_experiments.py`, `data/assessment_test_cases.json`, `docs/evaluation_protocol.md`, timestamped output CSV/JSON files. Run A/B/C/D on the same fixed test set. Include actual outputs, metrics, failures and a critical comparison. The AI variants require a valid API key. Human rating fields must remain blank until a person actually rates the outputs.

## Criterion 3: Reproducibility and documentation (5%)
Evidence: README, requirements, `.env.example`, prompt registry, scoring configuration, test cases and reproducibility guide. Record Python/package versions, prompt version, model ID, cache status, run date and any skipped/failed stages.

## Criterion 4: Ethics (15%)
Evidence: `docs/ethics_and_risk.md`. Describe a plausible deployed interface, identify two principles in full from the chosen ethics framework, and discuss at least three realistic lifecycle mechanisms, impacts, relevant concepts and explicit ethical positions. Confirm the exact full principle wording and source in the final presentation.

## Criterion 5: Reflection (15%)
Evidence: `docs/reflection_template.md`. Complete after experiments, in your own words. Include specific test IDs and measured results, technical issues, social implications, ethics, limitations and improvements. Do not submit the template unedited.

## Criterion 6: Professional communication and presentation (10%)
Evidence: `docs/assessment_demo_script.md` and `docs/presentation_10_minute_script.md`. Record a 10-minute video (maximum 12 minutes) showing the real app, intermediate outputs, experimental evidence, ethics, reflection and references.

## Submission gates

- [ ] Baseline runs independently and baseline artifacts remain unchanged.
- [ ] Unit tests run and their actual output is retained.
- [ ] Fixed test set has completed deterministic runs.
- [ ] AI variants have completed real Gemini runs if AI performance is claimed.
- [ ] Human ratings come from real evaluators and are recorded with a stated procedure.
- [ ] At least three approaches are compared and differences are analysed.
- [ ] Ethics analysis contains two principles and at least three developed examples.
- [ ] Reflection is written by the student and supported by observed evidence.
- [ ] Video is within the 10-minute target and under 12 minutes.
- [ ] References and source attribution are checked.

A project artifact or template is not evidence that a task has been completed. Mark a gate complete only after performing it and retaining evidence.
