"""Local backend-only JSONL audit trace for real pipeline runs.

Trace files may contain user-entered food preferences. They stay on the local machine;
do not commit or share logs without reviewing/redacting them first. API secrets are never
written. Set SMARTRECIPE_TRACE_ENABLED=false to disable trace persistence.
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
TRACE_PATH = ROOT / "logs" / "pipeline_trace.jsonl"

def write_pipeline_trace(payload: dict[str, Any]) -> str | None:
    enabled = os.getenv("SMARTRECIPE_TRACE_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}
    if not enabled:
        return None
    event = {"trace_id": str(uuid4()), "timestamp_utc": datetime.now(timezone.utc).isoformat(), **payload}
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TRACE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
    try:
        return str(TRACE_PATH.relative_to(ROOT))
    except ValueError:
        return str(TRACE_PATH)
