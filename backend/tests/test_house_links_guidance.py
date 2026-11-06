"""House Links guidance: remedies for thin fruit, and exchange meanings."""

from datetime import date

from agents.house_connections.core import analyze_all_houses
from agents.house_connections.guidance import exchange_meanings, house_remedies, lord_periods
from agents.house_connections.tables import timeline_table
from agents.natal_agent import calculate_natal_chart

AS_OF = date(2026, 11, 6)


def _chart() -> dict:
    return calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")


def test_remedies_only_for_thin_houses_one_lord_each():
    chart = _chart()
    remedies = house_remedies(chart, timeline_table(chart, AS_OF))
    assert sorted(remedies) == [1, 2, 7, 11, 12]
    assert {h: r["lord"] for h, r in remedies.items()} == {
        1: "Saturn", 2: "Jupiter", 7: "Sun", 11: "Jupiter", 12: "Saturn",
    }
    saturn = remedies[1]
    assert saturn["day"] == "Saturday" and saturn["count"] == 108
    assert "enemy's sign" in saturn["why_en"]
    assert all("gem" not in key for r in remedies.values() for key in r)


def test_remedy_timing_is_the_lords_next_period():
    chart = _chart()
    sun = house_remedies(chart, timeline_table(chart, AS_OF))[7]
    assert sun["when"][0] == {
        "label": "Sun bhukti in Moon mahadasha", "start": "7 Sep 2028", "end": "8 Mar 2029", "now": False,
    }


def test_exchange_meanings_chart_a():
    chart = _chart()
    out = exchange_meanings(analyze_all_houses(chart), timeline_table(chart, AS_OF))
    assert [(e["houses"], e["kind"]) for e in out] == [([2, 6], "dainya"), ([7, 8], "dainya")]
    two_six = out[0]
    assert "acts as if in its own sign" in two_six["meaning_en"]
    assert "The 2nd is drawn into health & service matters" in two_six["meaning_en"]
    assert two_six["active"][0]["label"] == "Moon mahadasha" and two_six["active"][0]["now"]


def test_lord_periods_skips_the_past():
    chart = _chart()
    periods = lord_periods({"Saturn"}, timeline_table(chart, AS_OF), limit=3)
    assert [p["label"] for p in periods] == [
        "Saturn bhukti in Mars mahadasha",
        "Saturn bhukti in Rahu mahadasha",
        "Saturn bhukti in Jupiter mahadasha",
    ]
