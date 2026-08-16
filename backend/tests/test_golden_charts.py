"""
Golden chart regression tests — fixed birth data with known Lahiri sidereal positions.
Reference: 18 Sep 1978, 17:35 IST, Chennai (13.0827°N, 80.2707°E).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import swisseph as swe

import ephemeris as eph
from agents.natal_agent import (
    calculate_natal_chart,
    _navamsa_sign_idx,
    _to_jd,
    SIGNS,
)
from ephemeris import RAHU_NODE

CHENNAI = (13.0827, 80.2707, "Asia/Kolkata")

GOLDEN_1978 = {
    "dob": "1978-09-18",
    "tob": "17:35",
    "ayanamsa_value": 23.5598,
    "ascendant": ("Aquarius", 22.65, "Purva Bhadrapada", 1),
    "planets": {
        "Sun":     ("Virgo", 1.66, "Uttara Phalguni", 2),
        "Moon":    ("Pisces", 24.14, "Revati", 3),
        "Mars":    ("Libra", 5.52, "Chitra", 4),
        "Mercury": ("Leo", 21.28, "Purva Phalguni", 3),
        "Jupiter": ("Cancer", 8.85, "Pushya", 2),
        "Venus":   ("Libra", 15.89, "Swati", 3),
        "Saturn":  ("Leo", 13.16, "Magha", 4),
        "Rahu":    ("Virgo", 3.20, "Uttara Phalguni", 2),
        "Ketu":    ("Pisces", 3.20, "Purva Bhadrapada", 4),
    },
}


def _calc_golden():
    lat, lon, tz = CHENNAI
    return calculate_natal_chart(GOLDEN_1978["dob"], GOLDEN_1978["tob"], lat, lon, tz)


def _golden_jd():
    _, _, tz = CHENNAI
    dt = datetime.strptime(
        f"{GOLDEN_1978['dob']} {GOLDEN_1978['tob']}:00",
        "%Y-%m-%d %H:%M:%S",
    ).replace(tzinfo=ZoneInfo(tz))
    return _to_jd(dt)


def test_golden_ayanamsa_lahiri():
    chart = _calc_golden()
    assert chart["ayanamsa"] == "Lahiri"
    assert abs(chart["ayanamsa_value"] - GOLDEN_1978["ayanamsa_value"]) < 0.01


def test_golden_ascendant():
    chart = _calc_golden()
    asc = chart["ascendant"]
    exp_sign, exp_deg, exp_nak, exp_pada = GOLDEN_1978["ascendant"]
    assert asc["sign"] == exp_sign
    assert abs(asc["degree_in_sign"] - exp_deg) < 0.05
    assert asc["nakshatra"] == exp_nak
    assert asc["pada"] == exp_pada


def test_golden_planet_positions():
    chart = _calc_golden()
    pp = chart["planet_positions"]
    for planet, (sign, deg, nak, pada) in GOLDEN_1978["planets"].items():
        pos = pp[planet]
        assert pos["sign"] == sign, f"{planet} sign"
        assert abs(pos["degree_in_sign"] - deg) < 0.05, f"{planet} degree"
        assert pos["nakshatra"] == nak, f"{planet} nakshatra"
        assert pos["pada"] == pada, f"{planet} pada"


def test_golden_moon_indices():
    chart = _calc_golden()
    assert chart["moon_nakshatra_index"] == 26  # Revati
    assert chart["moon_rasi_index"] == 11      # Pisces


def test_navamsa_positions_include_degree_and_nakshatra():
    chart = _calc_golden()
    nav = chart["navamsa_positions"]
    for planet, pos in nav.items():
        assert pos.get("degree_in_sign") is not None, f"{planet} missing D9 degree"
        assert pos.get("nakshatra"), f"{planet} missing D9 nakshatra"
        assert pos.get("pada") is not None, f"{planet} missing D9 pada"
        assert pos["sign_index"] == int(pos["longitude"] // 30) % 12


def test_rahu_uses_mean_node_not_true_node():
    assert RAHU_NODE == swe.MEAN_NODE
    assert RAHU_NODE != swe.TRUE_NODE
    chart = _calc_golden()
    assert chart.get("node_type") == "mean"
    rahu_lon = chart["planet_positions"]["Rahu"]["longitude"]
    ketu_lon = chart["planet_positions"]["Ketu"]["longitude"]
    mean = eph.calc_ut(
        _golden_jd(), swe.MEAN_NODE, swe.FLG_SIDEREAL | swe.FLG_SPEED
    )[0][0] % 360
    true = eph.calc_ut(
        _golden_jd(), swe.TRUE_NODE, swe.FLG_SIDEREAL | swe.FLG_SPEED
    )[0][0] % 360
    assert abs(rahu_lon - mean) < 1e-4
    assert abs(rahu_lon - true) > 1e-3
    assert abs(((ketu_lon - rahu_lon) % 360) - 180) < 1e-4


def test_navamsa_rahu_ketu_derived_from_d1_mean_node():
    chart = _calc_golden()
    pp = chart["planet_positions"]
    nav = chart["navamsa_positions"]
    for planet in ("Rahu", "Ketu"):
        d1_lon = pp[planet]["longitude"]
        expected_idx = _navamsa_sign_idx(d1_lon)
        assert nav[planet]["sign_index"] == expected_idx
        assert nav[planet]["sign"] == SIGNS[expected_idx]
    assert nav["Rahu"]["sign"] == "Capricorn"
    assert nav["Ketu"]["sign"] == "Cancer"
    assert abs((nav["Ketu"]["sign_index"] - nav["Rahu"]["sign_index"]) % 12) == 6
