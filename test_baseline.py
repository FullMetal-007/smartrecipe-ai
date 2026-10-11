"""Offline-safe smoke tests for the frozen baseline wrapper.
The large model is exercised manually by the Streamlit app and experiment runner.
"""
from pathlib import Path
from backend.baseline_service import recipe_tokenizer, baseline_service
from backend.config import SAMPLED_DATA_PATH, TFIDF_VECTORIZER_PATH, COMBINED_EMBEDDINGS_PATH

def test_baseline_artifacts_are_present():
    assert SAMPLED_DATA_PATH.exists()
    assert TFIDF_VECTORIZER_PATH.exists()
    assert COMBINED_EMBEDDINGS_PATH.exists()

def test_baseline_tokenizer_is_deterministic():
    assert recipe_tokenizer("Chicken, EGGS and tomatoes!") == recipe_tokenizer("chicken eggs tomatoes")

def test_baseline_service_starts_unloaded_without_loading_large_artifacts():
    service = type(baseline_service)()
    assert service._is_loaded is False
