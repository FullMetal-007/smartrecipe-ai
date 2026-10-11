import sys
import string
import ast
import pickle
from typing import List, Optional
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords

from backend.config import (
    SAMPLED_DATA_PATH,
    TFIDF_VECTORIZER_PATH,
    COMBINED_EMBEDDINGS_PATH
)
from backend.schemas import RecipeCandidate

# Prefer the original NLTK stopword corpus. In offline environments, use a
# bundled fallback rather than downloading resources during app startup.
# When the corpus exists, baseline tokenisation is identical to the source.
try:
    ENGLISH_STOP_WORDS = stopwords.words('english')
except LookupError:
    ENGLISH_STOP_WORDS = ("i me my myself we our ours ourselves you your yours yourself yourselves "
        "he him his himself she her hers herself it its itself they them their theirs themselves "
        "what which who whom this that these those am is are was were be been being have has had "
        "having do does did doing a an the and but if or because as until while of at by for with "
        "about against between into through during before after above below to from up down in out "
        "on off over under again further then once here there when where why how all any both each "
        "few more most other some such no nor not only own same so than too very s t can will just "
        "don should now d ll m o re ve y ain aren couldn didn doesn hadn hasn haven isn ma mightn "
        "mustn needn shan shouldn wasn weren won wouldn" ).split()

stemmer = nltk.stem.PorterStemmer()

def recipe_tokenizer(sentence: str) -> List[str]:
    """
    Exact tokenizer used in the frozen baseline model (app_reciperecs.py).
    Removes punctuation, lowercases, removes stopwords, and stems words.
    """
    for punctuation_mark in string.punctuation:
        sentence = sentence.replace(punctuation_mark, '').lower()

    listofwords = sentence.split(' ')
    listofstemmed_words = []

    for word in listofwords:
        if (word not in ENGLISH_STOP_WORDS) and (word != ''):
            stemmed_word = stemmer.stem(word)
            listofstemmed_words.append(stemmed_word)

    return listofstemmed_words

# Compatibility for legacy pickle artifacts created when the original app was run
# as a script. Such artifacts refer to `__main__.recipe_tokenizer`, which may not
# exist on Streamlit's current __main__ module during reruns.
class _BaselineCompatibilityUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == '__main__' and name == 'recipe_tokenizer':
            return recipe_tokenizer
        return super().find_class(module, name)


def _load_baseline_pickle(file_obj):
    # Keep the alias as a secondary compatibility path for libraries that inspect
    # __main__, while explicitly resolving the legacy tokenizer reference above.
    main_module = sys.modules.get('__main__')
    if main_module is not None:
        setattr(main_module, 'recipe_tokenizer', recipe_tokenizer)
    loaded = _BaselineCompatibilityUnpickler(file_obj).load()
    # Compatibility bridge for TF-IDF artifacts fitted by scikit-learn 0.24.x.
    # Newer releases expect the learned `idf_` attribute; old pickles store the
    # same values in `_idf_diag`. Reconstructing the public attribute from that
    # saved diagonal preserves the learned IDF values and does not refit the model.
    transformer = getattr(loaded, "_tfidf", None)
    if transformer is not None and hasattr(transformer, "_idf_diag") and not hasattr(transformer, "idf_"):
        transformer.idf_ = np.asarray(transformer._idf_diag.diagonal()).reshape(-1)
    return loaded


class BaselineRecommendationService:
    """
    Service wrapper around the frozen baseline recommendation system.
    Strictly preserves the original algorithm and feature representations.
    """

    def __init__(self):
        self._sampled_data: Optional[pd.DataFrame] = None
        self._vectorizer = None
        self._combined_embeddings: Optional[np.ndarray] = None
        self._is_loaded = False

    def load_models(self) -> None:
        """Loads baseline pickle artifacts into memory."""
        if self._is_loaded:
            return

        print("[BaselineService] Loading sampled_data.pkl...")
        self._sampled_data = pd.read_pickle(SAMPLED_DATA_PATH)

        print("[BaselineService] Loading tfidf_vectorizer.pkl...")
        with open(TFIDF_VECTORIZER_PATH, "rb") as f:
            self._vectorizer = _load_baseline_pickle(f)

        print("[BaselineService] Loading combined_embeddings.pkl...")
        with open(COMBINED_EMBEDDINGS_PATH, "rb") as f:
            self._combined_embeddings = _load_baseline_pickle(f)

        self._is_loaded = True
        print("[BaselineService] All baseline models successfully loaded.")

    def _parse_list_field(self, raw_val) -> List[str]:
        """Safely parses stringified list representations from the dataset."""
        if isinstance(raw_val, list):
            return [str(x).strip() for x in raw_val]
        if isinstance(raw_val, str):
            try:
                parsed = ast.literal_eval(raw_val)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed]
            except Exception:
                pass
            # Fallback string split
            cleaned = raw_val.replace('[', '').replace(']', '').replace("'", "").replace('"', '')
            return [x.strip() for x in cleaned.split(',') if x.strip()]
        return []

    def get_candidates(self, user_query: str, num_candidates: int = 5) -> List[RecipeCandidate]:
        """
        Executes the exact baseline recommendation algorithm:
        1. Tokenizes user input via recipe_tokenizer
        2. Vectorizes user text via TF-IDF vectorizer
        3. Zero-pads feature dimension to match combined_embeddings (5146)
        4. Computes cosine similarity across all 21,226 recipes
        5. Returns the top candidate recipes with rich metadata
        """
        if not self._is_loaded:
            self.load_models()

        # Step 1 & 2: Process and vectorize user input
        user_data = pd.DataFrame({'text_data': [user_query.lower()]})
        user_vectorized_data = self._vectorizer.transform(user_data['text_data'])

        # Step 3: Zero-pad if feature dimensions are missing
        num_missing_features = self._combined_embeddings.shape[1] - user_vectorized_data.shape[1]
        if num_missing_features > 0:
            user_vectorized_data = np.pad(
                user_vectorized_data.toarray(),
                ((0, 0), (0, num_missing_features))
            )

        # Step 4: Compute cosine similarity
        cosine_sim_matrix = cosine_similarity(user_vectorized_data, self._combined_embeddings)

        # Step 5: Retrieve top similar recipe indices
        similar_indices = cosine_sim_matrix[0].argsort()[::-1][:num_candidates]

        candidates: List[RecipeCandidate] = []
        for rank, idx in enumerate(similar_indices, start=1):
            row = self._sampled_data.iloc[idx]
            sim_score = float(cosine_sim_matrix[0][idx])

            ingredients = self._parse_list_field(row.get('ingredients', []))
            tags = self._parse_list_field(row.get('tags', []))

            # Extract nutritional / rating info safely
            calories = float(row['calories']) if pd.notnull(row.get('calories')) else None
            protein = float(row['protein']) if pd.notnull(row.get('protein')) else None
            rating = float(row['average_rating']) if pd.notnull(row.get('average_rating')) else None
            minutes = int(row['minutes']) if pd.notnull(row.get('minutes')) else 0
            desc = str(row.get('description', '')).strip()
            if not desc or desc == 'nan':
                desc = "No description provided."

            candidate = RecipeCandidate(
                name=str(row['name']),
                minutes=minutes,
                ingredients=ingredients,
                description=desc,
                tags=tags,
                calories=calories,
                protein=protein,
                average_rating=rating,
                baseline_rank=rank,
                baseline_similarity_score=round(sim_score, 4)
            )
            candidates.append(candidate)

        return candidates


# Singleton instance for easy import across backend
baseline_service = BaselineRecommendationService()
