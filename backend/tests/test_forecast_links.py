"""Forecast and Gochar read house status from House Links, with no scores."""

import json
from datetime import date

from agents.forecast_links import daily_context, forecast_links, gochara_result, house_context, public
from agents.house_connections.activation import compute_activation
from agents.house_connections.core import analyze_all_houses
from agents.house_connections.yogas import detect_yogas
from agents.natal_agent import calculate_natal_chart

DAY = "2026-11-06"


def _chart() -> dict:
    return calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")


def _links() -> dict:
    return forecast_links(_chart(), DAY, "12:00")


def test_status_matches_house_links_for_the_same_day():
    chart = _chart()
    houses = analyze_all_houses(chart)
    activation = compute_activation(chart, houses, detect_yogas(houses, chart), date(2026, 11, 6))
    expected = {r["house"]: r["status"]["key"] for r in activation["rows"]}
    got = {r["house"]: r["status"]["key"] for r in _links()["houses"]}
    assert got == expected


def test_by_status_covers_every_house_once():
    by = _links()["by_status"]
    assert sorted(h for hs in by.values() for h in hs) == list(range(1, 13))


def test_public_payload_has_no_scores():
    text = json.dumps(public(_links()))
    for word in ("score", "/100", "correlation", '"rag"'):
        assert word not in text


def test_gochara_result_follows_the_classical_table():
    assert gochara_result("Saturn", 3, False) == "favourable"
    assert gochara_result("Saturn", 3, True) == "blocked"
    assert gochara_result("Saturn", 8, False) == "unfavourable"
    assert gochara_result("Jupiter", 5, False) == "favourable"


def test_planet_rows_mark_dasha_lords():
    links = _links()
    md = links["period"]["mahadasha"]["planet"]
    roles = {r["planet"]: r["role"] for r in links["planets"]}
    assert roles[md] == "maha"


def test_house_prompt_separates_lordship_from_placement():
    one = house_context(_links(), 10)
    assert "Lord of the 10th: Mars" in one
    assert "Mars rules the 3rd and 10th" in one
    assert "Venus rules the 4th and 9th" in one
    assert "Transit on this date: Mars" in one


def test_moon_line_names_the_date_when_it_is_not_today():
    moon = _links()["moon_today"]
    assert moon["en"].startswith("On 6 Nov 2026 the Moon")


def test_prompt_blocks_carry_status_and_no_scores():
    links = _links()
    daily = daily_context(links)
    assert "HOUSE LINKS" in daily and "Live now" in daily
    one = house_context(links, 10)
    assert "Status on 2026-11-06" in one
    for block in (daily, one):
        assert "/100" not in block and "score" not in block.lower().replace("never quote a score", "")
