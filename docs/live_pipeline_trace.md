# Live recommendation pipeline trace

Every submitted Streamlit request renders a live, request-specific audit panel. It is designed to show the lecturer the actual data flowing between stages, not a static example.

## Stages

1. **Exact user request:** the original natural-language text.
2. **Parsed requirements:** structured ingredients, dietary preferences, time limit, meal type, servings and cuisine where detected.
3. **Frozen baseline output:** actual candidates before filtering, with baseline rank, similarity, source ingredients, time and nutrition fields. Local score fields are deliberately excluded from this snapshot.
4. **Hard constraint gate:** accepted and rejected candidates with reasons. A displayed recipe must contain every requested ingredient in the dataset ingredient list; title and tags do not count.
5. **Local scoring:** per-candidate 0–100 suitability score and the six component scores.
6. **AI ranking input:** secret-free preview of the exact candidate shortlist and constraints sent to Gemini.
7. **AI ranking output:** structured candidate scores, selection, validation result, and whether a correction was attempted.
8. **AI enrichment output:** actual generated recipe-card JSON or a visible skipped/error state.
9. **Runtime metadata:** model names, prompt versions, retrieval pool size, cache state, latencies, candidate counts and API call counts.

If no eligible candidate exists in the retrieved pool, the app reports no valid match and does not show non-matching recipes as final recommendations. For requests with multiple required ingredients, the retrieval pool is widened and can expand again when too few candidates pass. The baseline algorithm and saved artifacts are unchanged.

API keys are not included in the trace or logs. The AI preview is intentionally compact to reduce token usage.
