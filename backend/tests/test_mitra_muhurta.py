from datetime import datetime, timedelta

from dateutil.parser import parse

import ephemeris as swe
from agents.mitra_muhurta import compute_mitra_muhurta
from agents.natal_agent import calculate_natal_chart
from agents.panchangam_agent import LOCATIONS, _moon_lon, _to_jd
from agents.mitra_muhurta import _asc_lon, _bucket


def test_unknown_location_raises():
    try:
        compute_mitra_muhurta("Atlantis", "2026-11")
    except ValueError as exc:
        assert "Unknown location" in str(exc)
    else:
        raise AssertionError("expected unknown location")


def test_chennai_november_has_valid_overlaps():
    result = compute_mitra_muhurta("Chennai", "2026-11")
    loc = LOCATIONS["Chennai"]
    assert result["location"] == "Chennai"
    assert result["month"] == "2026-11"
    assert result["count"] == len(result["windows"])
    assert result["count"] >= 1
    ids = {row["id"] for row in result["windows"]}
    assert "ashwini_mesha" in ids
    assert "anusham_vrischika" in ids
    for row in result["windows"]:
        start = parse(row["start"])
        end = parse(row["end"])
        assert end > start
        assert start.strftime("%Y-%m") == "2026-11"
        mid = start + (end - start) / 2
        jd = _to_jd(mid if mid.tzinfo else mid.replace(tzinfo=start.tzinfo))
        nak = _bucket(_moon_lon(jd), 27)
        lag = _bucket(_asc_lon(jd, loc["lat"], loc["lon"]), 12)
        if row["id"] == "ashwini_mesha":
            assert nak == 0
            assert lag == 0
        else:
            assert nak == 16
            assert lag == 7


def test_month_defaults_to_location_today():
    from zoneinfo import ZoneInfo

    result = compute_mitra_muhurta("Chennai")
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    assert result["month"] == today.strftime("%Y-%m")


def test_invalid_month_raises():
    try:
        compute_mitra_muhurta("Chennai", "2026-13")
    except ValueError as exc:
        assert "Invalid month" in str(exc)
    else:
        raise AssertionError("expected invalid month")


def test_lagna_matches_natal_rising_sign_and_sign_edges():
    """Same Swiss/Lahiri rising degree as natal; windows sit inside the named lagna."""
    result = compute_mitra_muhurta("Chennai", "2026-11")
    loc = LOCATIONS["Chennai"]
    assert result["count"] >= 2
    for row in result["windows"]:
        start = parse(row["start"])
        end = parse(row["end"])
        mid = start + (end - start) / 2
        chart = calculate_natal_chart(
            mid.strftime("%Y-%m-%d"),
            mid.strftime("%H:%M:%S"),
            loc["lat"],
            loc["lon"],
            loc["tz"],
        )
        expected_sign = "Aries" if row["id"] == "ashwini_mesha" else "Scorpio"
        wanted_lag = 0 if row["id"] == "ashwini_mesha" else 7
        assert chart["ascendant"]["sign"] == expected_sign
        assert _bucket(_asc_lon(_to_jd(mid), loc["lat"], loc["lon"]), 12) == wanted_lag
        before = _bucket(_asc_lon(_to_jd(start - timedelta(seconds=30)), loc["lat"], loc["lon"]), 12)
        after = _bucket(_asc_lon(_to_jd(end + timedelta(seconds=30)), loc["lat"], loc["lon"]), 12)
        assert before != wanted_lag
        assert after != wanted_lag


def test_rising_degree_same_for_whole_sign_and_placidus():
    loc = LOCATIONS["Chennai"]
    jd = _to_jd(parse("2026-11-11T07:39:00+05:30"))
    whole = swe.houses_ex(jd, loc["lat"], loc["lon"], b"W", swe.FLG_SIDEREAL)[1][0]
    placidus = swe.houses_ex(jd, loc["lat"], loc["lon"], b"P", swe.FLG_SIDEREAL)[1][0]
    assert abs((whole - placidus + 180) % 360 - 180) < 1e-6
