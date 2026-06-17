"""Tamil predictive doshas — canonical fixture tests."""

from agents.tamil_dosha.mudakku import compute_mudakku
from agents.tamil_dosha.red_zones import compute_natal_red_zones
from agents.tamil_dosha.thithi_soonyam import compute_thithi_soonyam
from agents.tamil_dosha.utils import house_from_rasi, rasi_index_from_longitude


# Canonical fixture (audit spec):
# Lagna Kumbha (10), Sun Kanni nak 11 pada 4, Moon Meena nak 26, Tithi Dwitiya (2)
FIXTURE = {
    "lagna_rasi_index": 10,
    "sun_rasi_index": 5,
    "sun_nakshatra_index": 11,
    "sun_nakshatra_pada": 4,
    "moon_rasi_index": 11,
    "moon_nakshatra_index": 26,
    "tithi_index": 2,
}


def _moon_sun_lon_for_tithi(tithi_index: int) -> tuple[float, float]:
    """Sun at 150°, Moon offset for desired tithi index (Shukla paksha)."""
    sun_lon = 150.0
    if tithi_index == 0:
        moon_lon = sun_lon  # conjunction
    else:
        moon_lon = (sun_lon + (tithi_index * 12) - 6) % 360
    return moon_lon, sun_lon


def test_thithi_soonyam_canonical():
    moon_lon, sun_lon = _moon_sun_lon_for_tithi(2)
    result = compute_thithi_soonyam(
        moon_lon=moon_lon,
        sun_lon=sun_lon,
        lagna_rasi_index=10,
    )
    assert result["tithi_index"] == 2
    names = [r["name"] for r in result["dagdha_rasis"]]
    assert names == ["Dhanu", "Meena"]
    assert result["affected_houses"] == [11, 2]


def test_mudakku_method_a_canonical():
    result = compute_mudakku(
        moon_rasi_index=11,
        sun_rasi_index=5,
        sun_nakshatra_index=11,
        sun_nakshatra_pada=4,
        lagna_rasi_index=10,
    )["method_a"]
    assert result["rasi"]["name"] == "Simha"
    assert result["house"] == 7
    assert result["confidence"] == "UNVERIFIED"


def test_mudakku_method_b_canonical():
    result = compute_mudakku(
        moon_rasi_index=11,
        sun_rasi_index=5,
        sun_nakshatra_index=11,
        sun_nakshatra_pada=4,
        lagna_rasi_index=10,
    )["method_b"]
    assert result["rasi"]["name"] == "Meena"
    assert result["house"] == 2
    assert result["confidence"] == "MEDIUM"


def test_natal_vadhai_vainasikam_from_moon():
    # Moon at Revati (index 26)
    rz = compute_natal_red_zones(26)
    assert rz["janma_nakshatra"]["name"] == "Revati"
    # 7th from Revati: (26+6)%27 = 5 = Ardra
    assert rz["vadhai"]["name"] == "Ardra"
    assert rz["vadhai"]["ordinal"] == 7
    # 22nd from Revati: (26+21)%27 = 20 = Uttara Ashadha
    assert rz["vainasikam"]["name"] == "Uttara Ashadha"
    assert rz["vainasikam"]["ordinal"] == 22


def test_house_from_rasi_kumbha_lagna():
    assert house_from_rasi(8, 10) == 11  # Dhanu
    assert house_from_rasi(11, 10) == 2  # Meena


def test_shashti_variant_changes_dagdha():
    moon_lon, sun_lon = _moon_sun_lon_for_tithi(6)
    a = compute_thithi_soonyam(moon_lon=moon_lon, sun_lon=sun_lon, lagna_rasi_index=0, shashti_variant="mesha_simha")
    b = compute_thithi_soonyam(moon_lon=moon_lon, sun_lon=sun_lon, lagna_rasi_index=0, shashti_variant="mesha_kataka")
    assert [r["index"] for r in a["dagdha_rasis"]] == [0, 4]
    assert [r["index"] for r in b["dagdha_rasis"]] == [0, 3]


def test_tamil_dosha_agent_integration():
    from agents.tamil_dosha_agent import compute_tamil_doshas

    moon_lon, sun_lon = _moon_sun_lon_for_tithi(2)
    chart = {
        "ascendant": {"sign_index": 10, "sign": "Aquarius", "longitude": 300.0},
        "planet_positions": {
            "Sun": {
                "longitude": sun_lon,
                "sign_index": 5,
                "sign": "Virgo",
                "nakshatra": "Uttara Phalguni",
                "pada": 4,
                "house": 8,
            },
            "Moon": {
                "longitude": moon_lon,
                "sign_index": 11,
                "sign": "Pisces",
                "nakshatra": "Revati",
                "pada": 4,
                "house": 2,
            },
        },
    }
    out = compute_tamil_doshas(chart)
    assert out["thithi_soonyam"]["affected_houses"] == [11, 2]
    assert out["mudakku"]["method_a"]["rasi"]["name"] == "Simha"
    assert out["mudakku"]["method_b"]["rasi"]["name"] == "Meena"
    assert out["red_zones"]["vadhai"]["name"] == "Ardra"
    assert out["yogi"]["yogi_graha"] in {
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    }
