import json
from pathlib import Path
from backend import pipeline_trace

def test_trace_writer_persists_jsonl_without_secrets(tmp_path, monkeypatch):
    target = tmp_path / "logs" / "pipeline_trace.jsonl"
    monkeypatch.setattr(pipeline_trace, "TRACE_PATH", target)
    monkeypatch.setenv("SMARTRECIPE_TRACE_ENABLED", "true")
    relative = pipeline_trace.write_pipeline_trace({"query": "test query", "metadata": {"api_calls": 0}})
    assert relative.endswith("pipeline_trace.jsonl")
    event = json.loads(target.read_text(encoding="utf-8").strip())
    assert event["query"] == "test query"
    assert event["trace_id"]
    assert "api_key" not in json.dumps(event).lower()

def test_trace_writer_can_be_disabled(tmp_path, monkeypatch):
    target = tmp_path / "logs" / "pipeline_trace.jsonl"
    monkeypatch.setattr(pipeline_trace, "TRACE_PATH", target)
    monkeypatch.setenv("SMARTRECIPE_TRACE_ENABLED", "false")
    assert pipeline_trace.write_pipeline_trace({"query": "do not persist"}) is None
    assert not target.exists()
