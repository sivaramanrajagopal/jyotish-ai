"""The calendar feed is the all-day line and Rahu Kalam."""

from datetime import date

from agents.panchangam_calendar import build_panchangam_ics


def test_feed_has_the_day_and_rahu_only():
    body = build_panchangam_ics("Chennai", days=2, natal_nak=26, start=date(2026, 10, 10))

    assert "BEGIN:VCALENDAR" in body
    assert body.count("SUMMARY:Rahu Kalam") == 2
    assert "Shanivaram" in body
    assert "Tara " in body
    assert "Gulikai" not in body
    assert "Yamaganda" not in body
    assert "hora" not in body.lower()
    assert "TRANSP:OPAQUE" in body
    assert "TRIGGER:-PT10M" in body
    assert "DTSTART;VALUE=DATE:20261010" in body
