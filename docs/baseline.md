# Baseline system notes

The baseline assets are retained without modification:

* `input/sampled_data.pkl`
* `input/tfidf_vectorizer.pkl`
* `input/combined_embeddings.pkl`
* `app_reciperecs.py`

The wrapper in `backend/baseline_service.py` loads the artifacts and reproduces candidate retrieval using the saved vectorizer, the original combined embeddings, zero padding when needed, cosine similarity, and the requested top candidate pool. It adds structured metadata for the AI layer but does not retrain the baseline.

Run the original baseline interface separately with `streamlit run app_reciperecs.py` if needed. Run the SmartRecipe AI interface with `streamlit run streamlit_app.py`.
