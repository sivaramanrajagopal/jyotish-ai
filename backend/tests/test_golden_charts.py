"""
Golden chart regression tests — fixed birth data with known Lahiri sidereal positions.
Reference: 18 Sep 1978, 17:35 IST, Chennai (13.0827°N, 80.2707°E).
"""

from agents.natal_agent import calculate_natal_chart

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
        "Rahu":    ("Virgo", 3.18, "Uttara Phalguni", 2),
        "Ketu":    ("Pisces", 3.18, "Purva Bhadrapada", 4),
    },
}


def _calc_golden():
    lat, lon, tz = CHENNAI
    return calculate_natal_chart(GOLDEN_1978["dob"], GOLDEN_1978["tob"], lat, lon, tz)


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
