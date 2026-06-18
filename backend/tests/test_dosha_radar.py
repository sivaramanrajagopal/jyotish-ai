"""Dosha Radar — canonical fixture tests."""

from agents.dosha_radar.pushkara import check_pushkara, scan_pushkara_transit
from agents.dosha_radar.obstruction import get_mudakku_rasi, get_vadhai_vainasikam
from agents.dosha_radar_agent import compute_dosha_radar_analysis, dosha_radar_context_for_narrator
from agents.natal_agent import calculate_natal_chart

CHENNAI = {
    "dob": "1978-09-18",
    "tob": "17:35",
    "lat": 13.0827,
    "lon": 80.2707,
    "tz": "Asia/Kolkata",
}


def _chart():
    c = calculate_natal_chart(
        CHENNAI["dob"], CHENNAI["tob"],
        CHENNAI["lat"], CHENNAI["lon"], CHENNAI["tz"],
    )
    c["birth_data"] = {
        "dob": CHENNAI["dob"],
        "timezone": CHENNAI["tz"],
        "lat": CHENNAI["lat"],
        "lon": CHENNAI["lon"],
    }
    return c


def test_pushkara_zone_detection():
    # Bharani Pada 3 zone start
    pk = check_pushkara(21.0)
    assert pk["pushkara"] is True
    assert "Bharani" in pk["zone"]


def test_vadhai_vainasikam_offsets():
    vv = get_vadhai_vainasikam(0)
    assert vv["vadhai_idx"] == 6
    assert vv["vainasikam_idx"] == 21


def test_mudakku_rasi_shape():
    m = get_mudakku_rasi(120.5)
    assert "sign_idx" in m
    assert "sign_name" in m


def test_pushkara_transit_scan_shape():
    out = scan_pushkara_transit("Moon")
    assert "currently_pushkara" in out
    assert "next_entry_days" in out


def test_dosha_radar_analysis_structure():
    out = compute_dosha_radar_analysis(_chart())
    assert out["disclaimer"]["en"]
    assert out["tamil_blueprint"]["thithi_soonyam"]
    assert out["obstruction_profile"]["soonya_rasis"] is not None
    assert out["natal_afflictions"]["Moon"]
    assert out["transit_status"]["planets"]
    assert out["transit_highlights"] is not None
    assert out["forecast"]["days_ahead"] == 90
    assert isinstance(out["pushkara_transits"], list)
    assert out["summary"]["transit_date"]


def test_dosha_radar_narrator_context():
    ctx = dosha_radar_context_for_narrator(_chart())
    assert "DOSHA RADAR" in ctx
    assert "Pushkara" in ctx or "PUSHKARA" in ctx
