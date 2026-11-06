"""Panchangam limbs prevail at sunrise; end times run to the next sunrise and cross 360°."""

from datetime import date, timedelta

from dateutil.parser import parse

from agents.panchangam_agent import (
    NAKSHATRAS, TITHIS, YOGAS,
    _moon_lon, _moon_sun_diff, _moon_sun_sum, _to_jd,
    calculate_panchangam,
)


def _days(start: date, n: int):
    return [start + timedelta(days=i) for i in range(n)]


def test_limbs_match_sunrise_and_every_end_is_found():
    for d in _days(date(2026, 1, 1), 90):
        p = calculate_panchangam(d.isoformat(), "Chennai")
        jd = _to_jd(parse(p["sunrise"]))
        assert p["tithi_name"] == TITHIS[int(_moon_sun_diff(jd) / 12)]
        assert p["nakshatra_name"] == NAKSHATRAS[int(_moon_lon(jd) / (360 / 27))]
        assert p["yogam_name"] == YOGAS[int(_moon_sun_sum(jd) / (360 / 27))]
        for key in ("tithi_end_time", "nakshatra_end_time", "yogam_end_time", "karanam_end_time"):
            assert p[key], (d, key)
            assert parse(p[key]) > parse(p["sunrise"])


def test_wrap_limbs_get_end_times():
    seen = set()
    for d in _days(date(2026, 1, 1), 365):
        p = calculate_panchangam(d.isoformat(), "Chennai")
        for name, key in ((p["tithi_name"], "tithi_end_time"), (p["nakshatra_name"], "nakshatra_end_time"),
                          (p["yogam_name"], "yogam_end_time")):
            if name in ("Amavasya", "Revati", "Vaidhriti"):
                assert p[key], (d, name)
                seen.add(name)
    assert seen == {"Amavasya", "Revati", "Vaidhriti"}


def test_drik_reference_chennai_2026_11_06():
    p = calculate_panchangam("2026-11-06", "Chennai")
    assert (p["tithi_paksha"], p["tithi_name"]) == ("Krishna", "Dwadashi")
    assert p["nakshatra_name"] == "Hasta"
    assert p["yogam_name"] == "Vishkambha"
    assert parse(p["nakshatra_end_time"]).strftime("%Y-%m-%d %H:%M") == "2026-11-07 04:43"
    assert parse(p["yogam_end_time"]).strftime("%Y-%m-%d %H:%M") == "2026-11-07 04:10"


def test_erlangen_times_are_local():
    p = calculate_panchangam("2026-07-01", "Erlangen")
    assert p["timezone"] == "Europe/Berlin"
    assert parse(p["sunrise"]).utcoffset().total_seconds() == 2 * 3600
