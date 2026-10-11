# Local preference matching and low-token AI enhancement

- Frozen baseline model files and `app_reciperecs.py` remain byte-identical to the captured baseline manifest.
- For requests with multiple required ingredients, retrieve a wider baseline candidate pool; expand the pool once if too few candidates pass the gate.
- Required ingredients are verified against the dataset ingredient list only. Titles and tags do not satisfy a requirement, and processed items such as egg noodles or chicken stock do not count as whole eggs or chicken.
- Detectable dietary conflicts and known explicit time-limit violations are rejected before ranking. Unknown time values cannot be verified and are documented as a limitation.
- Eligible candidates receive a 0–100 local suitability score with a visible component breakdown. Initial weights are 30% ingredient utilisation, 30% constraint satisfaction, 15% time, 10% missing ingredients, 10% dietary/health fit, and 5% difficulty.
- Gemini receives a compact shortlist only. Ranking and cooking guidance use separate versioned prompts and separate caches. The normal path uses one ranking request plus one enrichment request when uncached; one correction request is possible if validation fails.
- Source ingredients remain separate from optional AI additions. Dataset time, ratings and nutrition are not rewritten by AI.
- Cooking steps and difficulty are AI suggestions, not verified source instructions.
- Pantry staples such as salt, pepper, water and cooking oil are displayed separately. AI failures expose a sanitized diagnostic without revealing the API key.
