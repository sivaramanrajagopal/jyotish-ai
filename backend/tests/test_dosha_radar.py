"""Dosha Radar — canonical fixture tests."""

import datetime

from agents.dosha_radar.afflictions import check_combustion
from agents.dosha_radar.pushkara import check_pushkara, scan_pushkara_transit
from agents.dosha_radar.obstruction import (
    build_obstruction_profile,
    compute_live_transit_status,
    get_mudakku_rasi,
    get_vadhai_vainasikam,
    scan_all_dosha_transits,
)
from agents.dosha_radar_agent import compute_dosha_radar_analysis, dosha_radar_context_for_narrator
from agents.natal_agent import calculate_natal_chart
from agents.tamil_dosha_agent import compute_tamil_doshas

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


def test_pushkara_seat_on_chennai():
    from agents.dosha_radar.pushkara import pushkara_seat

    chart = _chart()
    seats = {name: pushkara_seat(row["longitude"]) for name, row in chart["planet_positions"].items()}
    assert seats["Mercury"]["mark"] == "degree"
    assert seats["Jupiter"]["mark"] == "pada"
    assert seats["Jupiter"]["nakshatra"] == "Pushya"
    assert seats["Ketu"]["mark"] == "pada"
    assert seats["Sun"]["mark"] == ""
    assert chart["planet_positions"]["Mercury"]["pushkara"]["mark"] == "degree"
    assert chart["ascendant"]["pushkara"]["mark"] == ""


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


REF = datetime.datetime(2026, 11, 6, 20, 0, tzinfo=datetime.timezone.utc)


def swe_julday(dt: datetime.datetime) -> float:
    import ephemeris as swe

    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)


def _profile():
    chart = _chart()
    return build_obstruction_profile(chart, compute_tamil_doshas(chart))


def test_moon_nakshatra_entries_are_not_skipped():
    from agents.dosha_radar.obstruction import _FAVORABLE_TARAS, _jd, _nak_at, get_tara

    profile = _profile()
    out = scan_all_dosha_transits(profile, REF, days_ahead=90)
    moon = [e for e in out["red_zone_entries"] if e["planet"] == "Moon"]
    # 90 days is about 3.3 lunar months: one Vadhai and one Vainasikam entry each month.
    assert sum(e["type"] == "Vadhai" for e in moon) in (3, 4)
    assert sum(e["type"] == "Vainasikam" for e in moon) in (3, 4)

    def favourable(nak: int) -> bool:
        return get_tara(nak, profile["janma_nak_idx"])["tara_num"] in _FAVORABLE_TARAS

    ref_jd = _jd(REF)
    prev = _nak_at(ref_jd, "Moon")
    expected = int(favourable(prev))
    for hour in range(1, 90 * 24 + 1):
        nak = _nak_at(ref_jd + hour / 24, "Moon")
        if nak != prev and favourable(nak):
            expected += 1
        prev = nak
    assert len(out["tara_windows"]) == expected


def test_dates_are_in_the_chart_timezone():
    # 20:00 UTC on 6 Nov is 01:30 IST on 7 Nov.
    transit = compute_live_transit_status(_chart(), _profile(), REF, tz_name="Asia/Kolkata")
    assert transit["transit_date"] == "2026-11-07"


def test_moon_pushkara_entry_matches_an_hourly_search():
    from agents.dosha_radar.pushkara import _local_date, _lon_at

    out = scan_pushkara_transit("Moon", REF, tz_name="Asia/Kolkata")
    def inside(jd: float) -> bool:
        return check_pushkara(_lon_at(jd, "Moon"))["pushkara"]

    jd = swe_julday(REF)
    while inside(jd):
        jd += 1 / 24
    jd += 1 / 24
    while not inside(jd):
        jd += 1 / 24
    assert out["next_entry_date"] == _local_date(jd, "Asia/Kolkata")
    # 20:00 UTC on 6 Nov is already 7 Nov in India, so days count from 7 Nov.
    assert out["next_entry_days"] == (
        datetime.date.fromisoformat(out["next_entry_date"]) - datetime.date(2026, 11, 7)
    ).days


def test_pushkara_zone_edges_are_exact():
    assert check_pushkara(36.667)["pushkara"] is True
    assert check_pushkara(23.334)["pushkara"] is False


def test_nodes_are_never_combust_in_the_birth_chart():
    natal = compute_dosha_radar_analysis(_chart())["natal_afflictions"]
    for node in ("Rahu", "Ketu"):
        assert natal[node]["combust"]["combust"] is False
        assert natal[node]["critical_obstruction"]["severity"] == "none"


def test_retrograde_venus_uses_the_eight_degree_orb():
    assert check_combustion(0.0, 9.0, "Venus", False)["combust"] is True
    assert check_combustion(0.0, 9.0, "Venus", True)["combust"] is False


def test_dosha_radar_narrator_context():
    ctx = dosha_radar_context_for_narrator(_chart())
    assert "DOSHA RADAR" in ctx
    assert "Pushkara" in ctx or "PUSHKARA" in ctx
