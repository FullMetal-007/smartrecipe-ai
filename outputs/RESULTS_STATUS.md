# Results status

This package contains a reproducible test suite and experiment runner, not pre-fabricated successful results. Run `python -m pytest -q` and `python run_experiments.py` from the project root. The experiment runner writes timestamped per-case CSV/JSON plus an aggregate summary JSON under this directory.

The default run is offline and does not call Gemini. Run `python run_experiments.py --include-ai --limit 1` for a live smoke test, then `python run_experiments.py --include-ai` for the full live comparison. Configure a real key locally in `.env`; never add it to the archive. AI calls can incur charges.

Human relevance and usefulness ratings are intentionally blank until a person evaluates the outputs. Save test output, trace excerpts with personal data redacted, actual CSV/JSON results, and a short analysis of failures for assessment evidence.


## Baseline notebook and quota handling update

Use `baseline_model_validation.ipynb` to validate the saved runtime artifacts and run the baseline retrieval without Gemini. The experiment runner stops further AI requests after a quota/rate-limit error and records later AI stages as skipped. This prevents repeat calls but does not resolve provider quota limits.
