"""Offline tests for quota-aware experiment control; no Gemini calls are made."""
from run_experiments import _is_quota_exhaustion


def test_detects_gemini_resource_exhausted():
    exc = RuntimeError("ClientError: 429 RESOURCE_EXHAUSTED quota exceeded")
    assert _is_quota_exhaustion(exc)


def test_detects_rate_limit_wording():
    exc = RuntimeError("Too many requests: rate limit reached")
    assert _is_quota_exhaustion(exc)


def test_does_not_misclassify_unrelated_errors_as_quota():
    exc = RuntimeError("JSON schema validation failed")
    assert not _is_quota_exhaustion(exc)
