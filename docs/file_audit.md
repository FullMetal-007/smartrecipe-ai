# File audit and change boundary

## Protected baseline files

The following baseline artifacts are included unchanged in this distribution:

- `input/sampled_data.pkl`
- `input/tfidf_vectorizer.pkl`
- `input/combined_embeddings.pkl`
- `app_reciperecs.py` (original baseline application)

The baseline service is a wrapper around the existing TF-IDF vectorization, feature padding, cosine similarity, and top-candidate selection. The only robustness adjustment is an offline fallback for NLTK stopwords if the corpus is missing; when the corpus exists, the original NLTK stopword list is used.

## New or enhanced components

- Strict required-ingredient and detectable diet/time constraint gates.
- Transparent local score breakdown and reason strings.
- Separate AI ranking and recipe-enrichment prompts.
- Candidate identity and post-AI constraint validation.
- Live trace in the Streamlit interface.
- Fixed assessment test cases, experiment runner, evaluation protocol, rubric map, reproducibility notes and ethics analysis.

## Verification

Use `python test_artifact_integrity.py` to compare the SHA-256 hashes of the protected baseline files against the values captured when this package was assembled. A successful check establishes byte-level preservation for those files, not correctness of all project behavior.
