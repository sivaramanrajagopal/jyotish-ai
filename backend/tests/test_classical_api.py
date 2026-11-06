"""The classical route and chat tool, with the switch on and off."""

import json

from fastapi.testclient import TestClient

from agents.chat_tools import CLASSICAL_TOOL, TOOLS, active_tools, tool_result_json
from agents.natal_agent import calculate_natal_chart
from main import app

client = TestClient(app)


def _chart_a():
    chart = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    chart["birth_data"].update({"lat": 13.0827, "lon": 80.2707, "timezone": "Asia/Kolkata"})
    return chart


def test_route_returns_twelve_rules_for_a_guest_chart():
    r = client.post("/classical/matches", json={"natal_chart": _chart_a()})
    assert r.status_code == 200
    body = r.json()
    assert len(body["matches"]) == 12
    assert body["matches"][0]["source"]["cite"] == "BPHS 24.7"
    assert body["source"]["license"] == "Apache-2.0"


def test_route_needs_a_chart():
    assert client.post("/classical/matches", json={}).status_code == 400


def test_switch_off_hides_route_and_tool(monkeypatch):
    monkeypatch.setenv("CLASSICAL_RULES_ENABLED", "0")
    assert client.post("/classical/matches", json={"natal_chart": _chart_a()}).status_code == 404
    assert active_tools() == TOOLS
    assert "switched off" in tool_result_json("classical_rules", _chart_a())


class _FakeCompletions:
    """Asks for the classical tool once, then answers from what the tool returned."""

    def __init__(self, seen):
        self.seen = seen

    def create(self, **kwargs):
        from types import SimpleNamespace as NS

        self.seen.append(kwargs)
        tool_rows = [m for m in kwargs["messages"] if isinstance(m, dict) and m.get("role") == "tool"]
        if not tool_rows:
            call = NS(id="call-1", type="function", function=NS(name="classical_rules", arguments='{"house": 10}'))
            message = NS(
                content=None, tool_calls=[call],
                model_dump=lambda **_: {
                    "role": "assistant",
                    "tool_calls": [{"id": "call-1", "type": "function",
                                    "function": {"name": "classical_rules", "arguments": '{"house": 10}'}}],
                },
            )
        else:
            cites = [r["cite"] for r in json.loads(tool_rows[-1]["content"])["rules"]]
            message = NS(content="Classical view: " + ", ".join(cites), tool_calls=None)
        return NS(choices=[NS(message=message)])


def test_chat_calls_the_classical_tool_with_its_arguments(monkeypatch):
    from types import SimpleNamespace as NS

    import agents.chat_agent as chat_agent

    seen = []
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(chat_agent, "OpenAI", lambda **_: NS(chat=NS(completions=_FakeCompletions(seen))))
    reply = chat_agent.chat(_chart_a(), [{"role": "user", "content": "What does BPHS say about my career?"}])

    assert reply == "Classical view: BPHS 24.117"
    first = seen[0]
    assert "classical_rules" in [t["function"]["name"] for t in first["tools"]]
    assert "BPHS 24.7" in first["messages"][0]["content"]   # the guide's example cite is in the prompt


def test_chat_tool_is_offered_and_narrows_by_house():
    assert CLASSICAL_TOOL in active_tools()
    full = json.loads(tool_result_json("classical_rules", _chart_a()))
    assert len(full["rules"]) == 12

    tenth = json.loads(tool_result_json("classical_rules", _chart_a(), arguments='{"house": 10}'))
    assert {r["cite"] for r in tenth["rules"]} == {"BPHS 24.117"}
    assert all(r["why"] for r in tenth["rules"])

    foreign = json.loads(tool_result_json("classical_rules", _chart_a(), arguments='{"topic": "foreign"}'))
    # The 12th lord by house, and the 6th lord in the 2nd because its summary says "abroad".
    assert {r["cite"] for r in foreign["rules"]} == {"BPHS 24.139", "BPHS 24.62"}
