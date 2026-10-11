# Presentation plan and speaking notes (target 10 minutes; maximum 12)

Replace bracketed placeholders with your actual test outputs and metrics. Do not read placeholders aloud. Do not claim success where a run failed or was skipped.

## Slide 1 — Problem and motivation (0:00–0:50)
SmartRecipe AI explores whether an existing recipe recommender can be made more useful when people have specific ingredients and preferences. A similarity-based result can be topically related yet omit an ingredient the user explicitly asked to use. The prototype aims to improve relevance while preserving the original recommendation system for comparison.

## Slide 2 — User and industry context (0:50–1:35)
The intended users are home cooks trying to use ingredients they already have while considering preferences such as easy preparation, health goals and time. Expected input is natural language; expected output is a ranked shortlist with ingredient coverage, missing ingredients and clearly labelled AI suggestions. It is a prototype, not medical nutrition advice or a certified allergen checker.

## Slide 3 — Workflow and technologies (1:35–2:35)
Show the workflow: user request → structured requirements → original baseline candidates → hard constraint checks → local score → optional Gemini ranking → deterministic validation → optional correction → AI cooking guidance → final recipes. Explain the baseline artifacts and model are preserved. The application constructs the model prompt; users do not need to write one. Mention the configured model and prompt version actually used in your run.

## Slide 4 — Live demonstration (2:35–4:00)
Enter: “I have chicken and a few eggs. I want something healthy and easy to prepare.” Expand the live trace. Show the exact input and parsed requirements, actual baseline candidates before filtering, accepted/rejected candidates with reasons, score breakdown, AI request/response if configured, validation and final output. If no candidate contains both ingredients, the correct result is no valid match, not a false recommendation.

## Slide 5 — Experimental design (4:00–4:50)
Explain A: baseline; B: baseline plus AI ranking; C: constraints plus scoring plus AI ranking; D: C plus deterministic validation and one correction attempt. The same five test cases are used across versions. Explain why the conflict case tests whether the system handles incompatible requirements honestly.

## Slide 6 — Results (4:50–6:10)
Insert a screenshot/table from your actual timestamped experiment CSV. Report ingredient utilisation, constraint satisfaction, time compliance, missing required ingredients, latency and API calls. Include human relevance/usefulness averages only after real evaluators rate outputs. Explain at least one case that improved and one that did not, or state that no improvement was established.

## Slide 7 — Ethics (6:10–7:25)
Principle 1: Privacy and data governance. Example: free-text dietary/health details are sent to an external provider or retained in local logs longer than needed. Mechanism: request logging/cache and external API calls. Impact: disclosure of sensitive routines or health goals. Position: minimise fields, disclose processing, restrict retention and never commit logs/secrets.

Principle 2: Safety and accountability. Example 1: ingredient text matching misses an allergen or cross-contamination risk. Mechanism: dataset metadata lacks complete allergen data. Impact: users may trust an unsafe result. Position: never label results allergy-safe and tell users to verify labels. Example 2: generated steps are presented as verified source instructions. Mechanism: UI does not distinguish generated content. Impact: unsafe preparation or misplaced trust. Position: label suggestions, validate recipe identity and retain human responsibility.

Use the exact full principle text and source from the ethics framework selected for your course; cite it on this slide.

## Slide 8 — Critical reflection (7:25–8:45)
Discuss what worked and failed using actual test IDs and trace evidence. Address parser coverage, incomplete recipe metadata, candidate retrieval limitations, AI nondeterminism, API dependency/cost, caching, safety and bias in ingredient vocabularies. Explain what you would improve next and how you would evaluate that improvement. Do not use generic reflection without evidence.

## Slide 9 — Conclusion and references (8:45–10:00)
Summarise the measured result without overstating it. Distinguish implemented functionality from future work. Reference the original repository, datasets, Gemini documentation, course ethics framework and any other sources or third-party media used.

## Evidence to capture before recording
- Terminal output from pytest.
- Actual app request and baseline trace.
- A rejected candidate with a missing-ingredient reason.
- Actual Gemini response and validation, or the actual failure state.
- Timestamped A/B/C/D CSV and a small metrics comparison table.
- Completed human evaluation sheet if ratings are claimed.
- Screenshots of ethics and reflection slides and a final reference slide.
