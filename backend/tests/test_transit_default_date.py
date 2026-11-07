"""With no date given, transits are read for today in the birth timezone."""

from datetime import datetime
from zoneinfo import ZoneInfo

from agents.natal_agent import calculate_natal_chart
from agents.transit_score_agent import score_all_houses


def test_default_date_is_today_in_the_birth_timezone():
    tz = "America/Los_Angeles"
    chart = calculate_natal_chart("1985-03-10", "08:15", 34.0522, -118.2437, tz)
    result = score_all_houses(chart)
    today = datetime.now(ZoneInfo(tz)).date().isoformat()
    assert result["transit_date"] == today
    assert result["transit_moment"]["note"] == "current local time"
