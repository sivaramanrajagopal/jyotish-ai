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


def test_retired_model_message(monkeypatch):
    from ai_limits import AI_MODEL_GONE_DETAIL

    _env(monkeypatch, "AIzaTest")
    err = Exception("Error code: 404 - This model models/gemini-2.5-flash is no longer available to new users.")
    assert ai_error_detail(err) == AI_MODEL_GONE_DETAIL


def test_thinking_setting_is_dropped_when_rejected():
    import httpx
    from openai import BadRequestError
    from types import SimpleNamespace

    from ai_client import create_chat

    seen = []

    def create(**kw):
        seen.append(kw)
        if "extra_body" in kw:
            resp = httpx.Response(400, request=httpx.Request("POST", "http://x"))
            raise BadRequestError("reasoning_effort none is not supported", response=resp, body=None)
        return "ok"

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    assert create_chat(client, model="m", max_tokens=300, extra_body={"reasoning_effort": "none"}) == "ok"
    assert "extra_body" not in seen[-1] and seen[-1]["max_tokens"] == 2048


def _status_error(cls, code, message):
    import httpx

    return cls(message, response=httpx.Response(code, request=httpx.Request("POST", "http://x")), body=None)


def _client(create):
    from types import SimpleNamespace

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def test_busy_model_falls_back_to_lite(monkeypatch):
    from openai import InternalServerError

    from ai_client import create_chat

    _env(monkeypatch, "AIzaTest")
    seen = []

    def create(**kw):
        seen.append(kw["model"])
        if kw["model"] == "gemini-3.8-flash":
            raise _status_error(InternalServerError, 503, "high demand")
        return "ok"

    assert create_chat(_client(create), model="gemini-3.8-flash") == "ok"
    assert seen == ["gemini-3.8-flash", "gemini-flash-lite-latest"]


def test_busy_message_survives_a_failed_fallback(monkeypatch):
    from openai import InternalServerError, NotFoundError

    from ai_client import create_chat
    from ai_limits import AI_BUSY_DETAIL

    _env(monkeypatch, "AIzaTest")

    def create(**kw):
        if kw["model"] == "gemini-3.8-flash":
            raise _status_error(InternalServerError, 503, "This model is currently experiencing high demand.")
        raise _status_error(NotFoundError, 404, "model not found")

    try:
        create_chat(_client(create), model="gemini-3.8-flash")
    except InternalServerError as exc:
        assert ai_error_detail(exc) == AI_BUSY_DETAIL
    else:
        raise AssertionError("expected the busy error")


def test_openai_billing_message_stays(monkeypatch):
    _env(monkeypatch, "sk-test")
    assert ai_error_detail(Exception("billing_not_active")) == OPENAI_BILLING_DETAIL
    assert ai_error_detail(Exception("Rate limit reached for requests")) is None
