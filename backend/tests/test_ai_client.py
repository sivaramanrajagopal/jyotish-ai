"""The AI key decides the provider; Gemini errors get clear messages."""

from ai_client import GEMINI_BASE_URL, ai_base_url, ai_extra, ai_model
from ai_limits import AI_FREE_LIMIT_DETAIL, AI_KEY_INVALID_DETAIL, OPENAI_BILLING_DETAIL, ai_error_detail


def _env(monkeypatch, key, base="", model=""):
    monkeypatch.setenv("OPENAI_API_KEY", key)
    monkeypatch.setenv("AI_BASE_URL", base)
    monkeypatch.setenv("AI_MODEL", model)


def test_openai_key_keeps_openai(monkeypatch):
    _env(monkeypatch, "sk-test")
    assert ai_base_url() is None
    assert ai_model() == "gpt-4o-mini"
    assert ai_extra() == {}


def test_gemini_key_switches_endpoint_model_and_thinking(monkeypatch):
    _env(monkeypatch, "AIzaTest")
    assert ai_base_url() == GEMINI_BASE_URL
    assert ai_model().startswith("gemini-")
    assert ai_extra() == {"extra_body": {"reasoning_effort": "none"}}


def test_overrides_win(monkeypatch):
    _env(monkeypatch, "AIzaTest", model="gemini-2.5-flash-lite")
    assert ai_model() == "gemini-2.5-flash-lite"


def test_gemini_quota_and_bad_key_messages(monkeypatch):
    _env(monkeypatch, "AIzaTest")
    assert ai_error_detail(Exception("Error code: 429 - RESOURCE_EXHAUSTED")) == AI_FREE_LIMIT_DETAIL
    assert ai_error_detail(Exception("400 API key not valid. API_KEY_INVALID")) == AI_KEY_INVALID_DETAIL
    assert ai_error_detail(Exception("Error code: 400 - Please pass a valid API key")) == AI_KEY_INVALID_DETAIL


def test_openai_billing_message_stays(monkeypatch):
    _env(monkeypatch, "sk-test")
    assert ai_error_detail(Exception("billing_not_active")) == OPENAI_BILLING_DETAIL
    assert ai_error_detail(Exception("Rate limit reached for requests")) is None
