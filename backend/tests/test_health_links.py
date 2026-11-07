"""Health reads the health houses from House Links, at the same moment as Gochar and Forecast."""

from agents.forecast_links import forecast_links
from agents.health.links import HEALTH_HOUSES, health_links
from agents.health_agent import compute_health_analysis, health_context_for_narrator
from agents.life_cycle.themes import THEMES
from agents.natal_agent import calculate_natal_chart


def _chart() -> dict:
    return calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")


def test_health_houses_are_one_six_eight_twelve_everywhere():
    assert HEALTH_HOUSES == (1, 6, 8, 12)
    health = next(t for t in THEMES if t["key"] == "health")
    assert health["key_houses"] == [1, 6, 8, 12]


def test_health_status_matches_forecast_links():
    chart = _chart()
    links = health_links(chart)
    full = forecast_links(chart, None, None)
    expected = {r["house"]: r["status"]["key"] for r in full["houses"] if r["house"] in HEALTH_HOUSES}
    assert {r["house"]: r["status"]["key"] for r in links["houses"]} == expected
    assert sorted(h for hs in links["by_status"].values() for h in hs) == list(HEALTH_HOUSES)


def test_health_dasha_and_transit_date_follow_house_links():
    data = compute_health_analysis(_chart())
    period = data["house_links"]["period"]
    assert data["summary"]["maha_dasa"] == period["mahadasha"]["planet"]
    assert data["summary"]["bhukti"] == period["bhukti"]["planet"]
    assert data["summary"]["transit_date"] == data["house_links"]["transit_date"]


def test_planet_houses_are_whole_sign():
    chart = _chart()
    for p in chart["planet_positions"].values():
        p["house"] = 99
    rows = compute_health_analysis(chart)["planet_rows"]
    assert all(1 <= r["d1_house"] <= 12 for r in rows)


def test_health_still_loads_when_house_links_fail(monkeypatch):
    import agents.health_agent as health_agent

    def boom(_chart):
        raise RuntimeError("links down")

    monkeypatch.setattr(health_agent, "health_links", boom)
    data = compute_health_analysis(_chart())
    assert data["house_links"] is None
    assert data["summary"]["maha_dasa"]


def test_narrator_context_carries_house_links_status():
    text = health_context_for_narrator(_chart())
    assert "Health houses on House Links" in text
    assert "H8 " in text
