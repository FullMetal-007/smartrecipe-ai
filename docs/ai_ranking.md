# AI ranking implementation

Gemini receives a compact JSON payload containing the original natural-language request and a small candidate shortlist already retrieved by the frozen baseline. In the normal application, candidates are first filtered for hard constraints and locally scored. The response must evaluate every supplied candidate exactly once, preserve each candidate ID and name, and select an ID from the supplied set.

The ranking prompt is `backend/prompts/ai_ranking_v1.txt`; recipe-card generation uses the separate `backend/prompts/enrichment_v1.txt`. This separation prevents an instruction-writing prompt from being accidentally used for candidate ranking. Prompt versions are included in cache keys.

Gemini uses these starting dimensions: ingredient compatibility (30%), intent compatibility (30%), constraint satisfaction (30%), and practical suitability (10%). Python separately validates identity and measurable constraints. A single correction request may be made if deterministic validation fails.

The AI layer is optional for local operation. Without a valid key, the app can still demonstrate the frozen baseline, hard filtering, local score breakdown and live trace, but it clearly reports that AI ranking and cooking guidance were skipped.
