"""A failed AI request gives its quota use back; a successful one keeps it."""

import pytest
from fastapi.testclient import TestClient

import ai_limits
import main
from agents.natal_agent import calculate_natal_chart


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(ai_limits, "_SB", False)
    ai_limits._mem_anon.clear()
    return TestClient(main.app)


@pytest.fixture(scope="module")
def chart():
    c = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    c["birth_data"] = {
        "name": "Test", "dob": "1978-09-18", "tob": "17:35",
        "timezone": "Asia/Kolkata", "lat": 13.0827, "lon": 80.2707,
    }
    return c


def _guest_chats() -> int:
    return sum(c.get("chat_count", 0) for c in ai_limits._mem_anon.values())


def _ask(client, chart):
    return client.post("/chat", json={
        "natal_chart": chart,
        "messages": [{"role": "user", "content": "How is my career?"}],
    })


def test_failed_chat_is_refunded(client, chart, monkeypatch):
    def fail(**_):
        raise RuntimeError("OpenAI account has no credits remaining.")

    monkeypatch.setattr(main, "jyotish_chat", fail)
    assert _ask(client, chart).status_code == 503
    assert _guest_chats() == 0


def test_successful_chat_is_counted(client, chart, monkeypatch):
    monkeypatch.setattr(main, "jyotish_chat", lambda **_: "A reading.")
    assert _ask(client, chart).status_code == 200
    assert _guest_chats() == 1


def test_limit_still_enforced(client, chart, monkeypatch):
    monkeypatch.setattr(main, "jyotish_chat", lambda **_: "A reading.")
    monkeypatch.setattr(ai_limits, "ANON_DAILY_CHAT_LIMIT", 1)
    assert _ask(client, chart).status_code == 200
    assert _ask(client, chart).status_code == 429
    assert _guest_chats() == 1
