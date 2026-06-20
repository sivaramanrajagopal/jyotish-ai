"""Tests for Shodhya Pinda trigger nakshatra status."""

from datetime import date

from agents.ashtakavarga_agent import compute_trigger_status
from agents.natal_agent import calculate_natal_chart


CHENNAI_CHART = calculate_natal_chart(
    "1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata"
)


def test_trigger_status_structure():
    result = compute_trigger_status(CHENNAI_CHART, timezone="Asia/Kolkata")
    assert result["available"] is True
    assert result["today_moon_nak"]
    assert isinstance(result["is_trigger_day"], bool)
    assert len(result["all_triggers"]) == 7
    for item in result["all_triggers"]:
        assert item["planet"] in {"SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"}
        assert item["trigger_nakshatra"]
        assert item["shodhya_pinda"] > 0
        assert item["pinda_category"] in {"Developing", "Moderate", "Strong", "Exceptional"}
        assert item["houses_ruled"]


def test_chennai_hasta_hotspot():
    result = compute_trigger_status(CHENNAI_CHART, timezone="Asia/Kolkata")
    hasta = next(h for h in result["hotspots"] if h["nakshatra"] == "Hasta")
    assert hasta["planet_count"] == 3
    assert hasta["is_triple_trigger"] is True
    assert set(hasta["planets"]) == {"MARS", "MERCURY", "JUPITER"}


def test_active_planets_when_moon_in_hasta():
    # Force evaluation on a day when Moon is in Hasta (scan until found)
    for offset in range(28):
        day = date.today()
        from datetime import timedelta
        day = day + timedelta(days=offset)
        result = compute_trigger_status(CHENNAI_CHART, target_date=day, timezone="Asia/Kolkata")
        if result["today_moon_nak"] == "Hasta":
            assert result["is_trigger_day"] is True
            assert len(result["active_planets"]) == 3
            assert result["active_nakshatra"] == "Hasta"
            return
    raise AssertionError("Moon did not enter Hasta within 28 days")


def test_next_trigger_when_not_active():
    for offset in range(28):
        from datetime import timedelta
        day = date.today() + timedelta(days=offset)
        result = compute_trigger_status(CHENNAI_CHART, target_date=day, timezone="Asia/Kolkata")
        if not result["is_trigger_day"]:
            assert result["next_trigger"] is not None
            assert result["next_trigger"]["days_until"] >= 0
            assert result["next_trigger"]["nakshatra"]
            assert result["next_trigger"]["planets"]
            return
    raise AssertionError("Every day was a trigger day in scan window")
