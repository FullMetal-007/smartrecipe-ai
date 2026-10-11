# Backend-only pipeline trace and assessment metrics

## Private trace

The Streamlit interface now shows only recipe results and user-safe status messages. Full per-request diagnostics are recorded by `backend/pipeline_trace.py` in `logs/pipeline_trace.jsonl`, one JSON object per line. The trace includes the exact input, parsed requirements, baseline candidates, hard-gate accepted/rejected candidates and reasons, local scores, safe AI request preview, AI output, validation, enrichment output, errors and latency/API metadata. It never writes the Gemini key.

The trace is local developer/assessment evidence, not an authentication-protected admin service. Anyone with access to the computer and project folder can read it. It may contain the user's exact food request, so review and redact it before sharing. `logs/` is ignored by Git. Set `SMARTRECIPE_TRACE_ENABLED=false` in the process environment to disable persistence.

## Reproduce tests

From the project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe run_experiments.py
```

The offline experiment run produces per-case CSV/JSON and a computed summary JSON under `outputs/`. It does not call Gemini. AI variant experiments require a valid local `.env` key and can incur API charges:

```powershell
.\.venv\Scripts\python.exe run_experiments.py --include-ai --limit 1
.\.venv\Scripts\python.exe run_experiments.py --include-ai
```

Metrics include ingredient utilisation, hard-constraint satisfaction, time compliance, diet compliance, missing required ingredients, candidate availability, latency and API calls. Human relevance/usefulness ratings remain blank until an evaluator actually rates outputs. Metrics are computed from the run and are not prefilled claims.

## Interpreting no-match outcomes

A no-match result can be correct (for example, chicken with a strict vegan requirement) or indicate that retrieval, parsing or the dataset needs improvement. Inspect the local JSONL trace to distinguish these cases. Do not remove safety gates simply to increase the number of returned recipes.
