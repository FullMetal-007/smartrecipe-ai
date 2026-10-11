"""Append-only experiment logging. Secrets are never logged."""
import json
from pathlib import Path
from backend.config import EXPERIMENT_LOG_DIR
from backend.schemas import ExperimentRecord

def log_experiment(record: ExperimentRecord) -> Path:
    EXPERIMENT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    path=EXPERIMENT_LOG_DIR / "experiments.jsonl"
    with path.open("a",encoding="utf-8") as f:
        f.write(record.model_dump_json() + "\n")
    return path
