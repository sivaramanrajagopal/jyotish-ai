"""Ask AI system prompt: one rule set, local times, exact Chandrashtama, bounded tool loop."""

import datetime
import re
from types import SimpleNamespace

import pytest

import agents.chat_agent as ca
from agents.dosha_radar.obstruction import _jd, _moon_sign_at, find_chandrashtama_windows
from agents.natal_agent import calculate_natal_chart
from chart_utils import refresh_dasha


@pytest.fixture(scope="module")
def chart():
    c = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    c["birth_data"] = {
        "name": "Test", "dob": "1978-09-18", "tob": "17:35",
        "timezone": "Asia/Kolkata", "lat": 13.0827, "lon": 80.2707,
    }
    return refresh_dasha(c, force=True)


@pytest.fixture(scope="module")
def prompt(chart):
    return ca._build_system(chart, "Chennai", user_message="When will things improve in the next few years?")


def test_no_transit_scores_or_block_disclaimers(prompt):
    assert not re.search(r"\d+\s*/\s*100", prompt)
    assert "cite the house score" not in prompt
    assert "direct_transit" not in prompt
    assert not any(line.lstrip().startswith("DISCLAIMER") for line in prompt.split("\n"))
    assert "Whether a house is live or quiet comes from the HOUSE CONNECTIONS block" in prompt
    assert "On health questions only, close with one short line" in prompt


def test_gochara_block_separates_occupants_from_aspects(prompt):
    block = prompt[prompt.index("=== GOCHARA"):]
    assert "TRANSITS (sign" in block
    assert re.search(r"H1 [^\n]*in the house: [^\n]*", block) or re.search(r"H1 [^\n]*aspecting: ", block)


def test_panchangam_uses_location_time_with_end_times(chart):
    erl = ca._build_system(chart, "Erlangen", user_message="hi")
    today = erl[erl.index("=== TODAY'S PANCHANGAM"):erl.index("=== PERSONAL PANCHANGAM")]
    assert "Europe/Berlin" in today
    assert "IST" not in today
    for limb in ("Tithi", "Nakshatra", "Yogam", "Karanam"):
        line = next(l for l in today.split("\n") if l.startswith(limb))
        assert "ends" in line and "then" in line


def test_tara_calendar_is_next_30_days(prompt):
    block = prompt[prompt.index("=== TARA BALAM CALENDAR"):].split("\n\n")[0]
    assert len([l for l in block.split("\n") if re.match(r"\s+[A-Z][a-z]{2} \d{2} \[", l)]) == 30


def test_chandrashtama_windows_start_and_end_at_sign_change():
    ref = datetime.datetime(2026, 11, 7, 0, 30, tzinfo=datetime.timezone.utc)
    libra = 6
    windows = find_chandrashtama_windows(libra, _jd(ref), 60, "Asia/Kolkata")
    assert len(windows) >= 2
    one_min = 1.0 / 1440
    for w in windows:
        for key, inside in (("start_time", 1), ("end_time", -1)):
            t = datetime.datetime.fromisoformat(w[key]).astimezone(datetime.timezone.utc)
            jd = _jd(t)
            assert _moon_sign_at(jd + 2 * one_min * inside) == libra
            assert _moon_sign_at(jd - 2 * one_min * inside) != libra
    first = windows[0]
    assert first["start_time"].startswith("2026-11-07T17:1")
    assert first["end_time"].startswith("2026-11-10T02:")


def test_chat_always_answers_after_tool_rounds(chart, monkeypatch):
    calls = []

    def fake_create(**kwargs):
        calls.append(kwargs.get("tool_choice"))
        if kwargs.get("tool_choice") == "none":
            msg = SimpleNamespace(content="Final answer.", tool_calls=None,
                                  model_dump=lambda **_: {"role": "assistant", "content": "Final answer."})
        else:
            call = SimpleNamespace(id="c1", function=SimpleNamespace(name="current_period", arguments="{}"))
            msg = SimpleNamespace(content="", tool_calls=[call],
                                  model_dump=lambda **_: {"role": "assistant", "content": "", "tool_calls": []})
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])

    class FakeClient:
        def __init__(self, **_):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=fake_create))

    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(ca, "OpenAI", FakeClient)
    monkeypatch.setattr("agents.chat_tools.tool_result_json", lambda *a, **k: "{}")
    reply = ca.chat(chart, [{"role": "user", "content": "How is my career?"}])
    assert reply == "Final answer."
    assert calls[-1] == "none"
    assert len(calls) == 4
