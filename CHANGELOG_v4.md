# SmartRecipe AI v4 changes

- Centralised all recommendation processing in `backend/pipeline.py`; Streamlit is now a presentation layer that renders the backend's structured pipeline stages.
- Added strict ingredient matching using dataset ingredient lists only. Recipe names, descriptions and tags cannot satisfy an ingredient requirement.
- Added exclusions so words in products such as `egg noodles` or `chicken stock` do not falsely satisfy requests for eggs or chicken meat.
- Added overlap-aware requirement parsing for compound ingredients such as bell pepper, ground beef, cream cheese and chicken stock.
- Added hard gates for missing requested ingredients, detectable dietary conflicts and known cooking times above an explicit limit.
- Added transparent 0–100 local scoring with component breakdown and documented initial weights.
- Added separate, versioned AI ranking, correction and recipe-enrichment prompts; fixed the earlier risk of using a recipe-card prompt for ranking.
- Added AI candidate identity checks, deterministic post-validation, and at most one correction attempt when enabled.
- Added a live nine-stage lecturer trace for the actual request, baseline output, constraints, local scores, AI input/output, validation, enrichment and runtime metadata.
- Added fixed test cases, A/B/C/D experiment runner, actual-results CSV/JSON output, human evaluation template, rubric evidence map, ethics analysis, reproducibility notes, and a demonstration script.
- Added an offline compatibility bridge for older saved TF-IDF artifacts and an artifact hash guard to detect accidental changes to protected baseline files.
- Added tests for strict ingredient gates, compound phrase parsing, time constraints, scoring, conflicting requirements, pipeline behavior, and baseline artifact integrity.

No API key is included. Live Gemini behavior still requires a valid local `.env` key and must be tested in the user's own environment. No human ratings or experimental superiority claims are fabricated.
