# Reproducibility and local setup

## Requirements

- Windows 10/11 or another supported Python environment.
- Python 3.10 is recommended for compatibility with the saved baseline artifacts.
- The project files, including `input/sampled_data.pkl`, `input/tfidf_vectorizer.pkl`, and `input/combined_embeddings.pkl`.
- Gemini API key only for live AI ranking/enrichment experiments. The deterministic baseline and constraint pipeline do not require a key.

## Windows PowerShell setup

Run commands from the folder containing `streamlit_app.py`.

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Add `GEMINI_API_KEY=...` to `.env` only if you want live Gemini calls. Keep the key private. If PowerShell activation is blocked, do not activate the environment; invoke `.venv\Scripts\python.exe` directly.

## Run the application and tests

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe run_experiments.py
```

To run real AI variants, use `python run_experiments.py --include-ai`. This performs external Gemini requests and may incur usage charges. A cache hit is reported separately. Do not treat skipped AI variants as evaluated results.

## Reproduce the lecture demonstration

1. Start the app and enter one of the exact cases from `data/assessment_test_cases.json`.
2. Expand **Live pipeline trace**.
3. Inspect the original baseline candidates before the gate, including source ingredient lists and baseline similarity.
4. Inspect accepted and rejected candidates and the rejection reasons.
5. Inspect local score breakdown, AI input preview, ranking output, validation result, enrichment output and runtime metadata.
6. Re-run the same query to demonstrate cache behavior and compare the trace.
7. Run `run_experiments.py` and open the generated timestamped CSV.

## Offline dependency note

When the NLTK stopwords corpus is available, the baseline tokenizer uses it. If the corpus is unavailable and network access is blocked, a bundled fallback list prevents startup from failing. For strict reproduction across machines, install the NLTK stopwords corpus and record whether the fallback was used.

## Saved scikit-learn artifact compatibility

The bundled TF-IDF vectorizer was serialized with scikit-learn 0.24.1, while the project dependency file targets scikit-learn 1.0.2. `backend/baseline_service.py` includes a small compatibility bridge that reconstructs the public `idf_` values from the existing saved `_idf_diag` when needed; it does not refit or rewrite the artifact. A hash test guards the saved files. If a scikit-learn version warning appears, record the version in your experiment notes. For best reproducibility, use the documented Python environment and verify that the original baseline app works before presenting results.
