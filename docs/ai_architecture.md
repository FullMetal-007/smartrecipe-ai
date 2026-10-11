# AI architecture and experiment variants

The project preserves the existing baseline and adds several independent stages around it. See `architecture.md` for the end-to-end diagram.

## Runtime path

1. Parse explicit requirements from natural language.
2. Run the original baseline candidate retrieval.
3. Reject candidates missing any required ingredient in their dataset ingredient list, violating a detectable diet preference, or exceeding a known explicit time limit.
4. Apply a documented local score to eligible candidates.
5. If Gemini is configured, rank only the eligible candidate set.
6. Validate candidate identity and explicit constraints. Make at most one correction attempt when validation fails.
7. Enrich the final list with concise suggested cooking guidance.
8. Display the live trace and append experiment metadata.

## Experiment variants

- **A:** baseline only.
- **B:** baseline plus AI ranking, without pre-filtering, so failures can be measured.
- **C:** hard constraint gate, local scoring and AI ranking.
- **D:** C plus post-AI validation and one correction attempt if required.

The experiment runner keeps A and B as comparison variants only. The normal application never displays a candidate that fails its final hard-constraint gate.

## Cost and failure handling

Ranking and enrichment are separate structured calls and are cached independently. A new uncached request normally uses one ranking call and one enrichment call; a validation correction may add one ranking call. Repeated identical requests can hit local cache. Missing credentials or API errors are shown explicitly. A failed AI stage is not reported as successful AI output.

## Validation scope

Python validates selected candidate membership, required ingredients, known time limits, and detectable diet conflicts using source ingredient data. These checks cannot certify allergy safety, medical nutrition suitability, exact recipe correctness, or cross-contamination safety.
