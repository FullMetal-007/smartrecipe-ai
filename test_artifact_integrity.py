"""Byte-level guard for the protected baseline model and source app."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "input/sampled_data.pkl": "e7e6404e22979dd56ee3d1dfcd8e64cab7323a1ab704d66eb741ca26c1185d39",
    "input/tfidf_vectorizer.pkl": "33d1df3b37bac6bca612bb4db78ca50b7e10fa40f5d127fceccd53529ae8c690",
    "input/combined_embeddings.pkl": "081af1b18ebfa7bd2aef4536d2b814fb293421e77bbdb592180ba2b11ad64bcd",
    "app_reciperecs.py": "82168080dc19fadfe9312e6617144e04668279b2b29ef8b62acb49e305772a0b",
}

def test_protected_baseline_files_match_package_manifest():
    for relative, expected in EXPECTED.items():
        path = ROOT / relative
        assert path.is_file(), f"Protected baseline file is missing: {relative}"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == expected, f"Protected baseline file changed: {relative}"
