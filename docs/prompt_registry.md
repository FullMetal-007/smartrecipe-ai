# Prompt registry

| Stage | File | Version setting | Purpose |
|---|---|---|---|
| AI candidate ranking | `backend/prompts/ai_ranking_v1.txt` | `RANKING_PROMPT_VERSION=v1` | Rank only baseline candidates and provide candidate scores. |
| AI correction | `backend/prompts/correction_v1.txt` | `RANKING_PROMPT_VERSION=v1` | Optional single retry after deterministic validation failure. |
| Recipe-card enrichment | `backend/prompts/enrichment_v1.txt` | `PROMPT_VERSION=v1` | Add cooking guidance without changing recipe identity or order. |

The ranking prompt and enrichment prompt are deliberately separate. This prevents an enrichment-only prompt from accidentally being used for ranking. Change the relevant version when editing a prompt so cache keys do not reuse responses from an older prompt. Legacy `ranking_v1.txt`, `ranking_v2.txt`, and `ranking_v3.txt` are retained as development history only.
