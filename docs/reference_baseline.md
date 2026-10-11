# Baseline provenance and attribution

SmartRecipe AI builds on the recipe recommendation approach and project structure of the public recipe recommender reference at:

https://github.com/kli210/recipe_recommender_capstone

The original baseline application and saved assets are retained for provenance and reproducibility. The original retrieval workflow uses TF IDF vectorization, a combined embedding representation, cosine similarity, and a recipe dataset to retrieve candidates. The reference repository and its original author retain credit for that baseline work. Check the source repository's license and attribution requirements before redistribution or publication.

## Boundary of work

**Baseline components retained:** `app_reciperecs.py`, `input/sampled_data.pkl`, `input/tfidf_vectorizer.pkl`, and `input/combined_embeddings.pkl`.

**SmartRecipe AI additions:** a separate Streamlit interface, candidate service wrapper, Gemini ranking provider, structured response validation, deterministic constraint checks, caching, experiment logging, and assessment focused documentation.

The interface is branded SmartRecipe AI, but the project does not claim that the original recommender or its underlying dataset was created from scratch for this assessment.
