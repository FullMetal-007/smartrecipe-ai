# Live demonstration script

Suggested duration: 5 to 7 minutes. Demonstrate the actual application; do not read these notes as if they were test results.

1. **Problem and motivation (30 seconds):** the baseline ranks by textual similarity and can return a recipe missing one of the ingredients the user explicitly requested.
2. **Show the input (30 seconds):** enter “I have chicken and a few eggs. I want something healthy and easy to prepare.”
3. **Show the baseline (45 seconds):** expand the live trace and point to Stage 3. Explain that these are actual baseline candidates before any new filters or scores.
4. **Show hard validation (45 seconds):** point to Stage 4. Demonstrate that a chicken-only or egg-only recipe is rejected when both are required. If no joint-match recipe exists in the retrieved dataset, show the no-match message instead of claiming success.
5. **Show local scoring (45 seconds):** explain the weights and visible breakdown in Stage 5. State that weights are a starting configuration, not an empirically optimal solution.
6. **Show AI use (60 seconds):** with a valid `.env` key, point to the compact AI ranking input, the actual structured response, deterministic validation, and recipe-card enrichment. Mention caching and call count. Without a key, honestly show that AI is skipped and do not claim a live AI result.
7. **Show evaluation (60 seconds):** run `python run_experiments.py --include-ai` when key and time allow, then open the actual CSV. Compare A/B/C/D on the same test cases, including the conflict case. Do not invent human ratings or performance improvements.
8. **Ethics and reflection (45 seconds):** discuss privacy and external processing, inaccurate ingredient/diet checks, generated instruction limits, and the current parser/dataset limitations.
9. **Close (15 seconds):** summarise what is demonstrably implemented and what remains future work.

## Evidence to capture

- User input and raw baseline output cell.
- Hard gate accepted/rejected output.
- Local score breakdown.
- AI request preview and actual response or actual failure state.
- Final output and runtime/caching metadata.
- Actual experiment CSV and unit test output.
