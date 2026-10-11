"""Central configuration for SmartRecipe AI."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
INPUT_DIR = BASE_DIR / "input"
SAMPLED_DATA_PATH = INPUT_DIR / "sampled_data.pkl"
TFIDF_VECTORIZER_PATH = INPUT_DIR / "tfidf_vectorizer.pkl"
COMBINED_EMBEDDINGS_PATH = INPUT_DIR / "combined_embeddings.pkl"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.2"))
NUM_CANDIDATES = 5
NUM_RETRIEVAL_CANDIDATES = max(10, int(os.getenv("NUM_RETRIEVAL_CANDIDATES", "100")))
MAX_RETRIEVAL_CANDIDATES = max(NUM_RETRIEVAL_CANDIDATES, min(21226, int(os.getenv("MAX_RETRIEVAL_CANDIDATES", "5000"))))
AI_CACHE_ENABLED = os.getenv("AI_CACHE_ENABLED", "true").lower() == "true"
CACHE_DIR = BASE_DIR / ".ai_cache"
PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v1")
RANKING_PROMPT_VERSION = os.getenv("RANKING_PROMPT_VERSION", "v1")
PROMPTS_DIR = BASE_DIR / "backend" / "prompts"
CONFIG_VERSION = os.getenv("CONFIG_VERSION", "1.1.0")
MAX_CORRECTION_ATTEMPTS = max(0, min(1, int(os.getenv("MAX_CORRECTION_ATTEMPTS", "1"))))
EXPERIMENT_LOG_DIR = BASE_DIR / "logs"
