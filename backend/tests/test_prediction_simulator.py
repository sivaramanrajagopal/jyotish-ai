"""Tests for Life Cycle Simulator (Phase 1)."""

import datetime

from agents.natal_agent import calculate_natal_chart
from agents.prediction_simulator import compute_life_cycle_simulation
from chart_utils import ensure_dasha

# Golden reference chart (Chennai) — use project test fixture
GOLDEN = {
    "dob": "1978-09-18",
    "tob": "17:35",
    "lat": 13.0827,
    "lon": 80.2707,
    "tz": "Asia/Kolkata",
}


def _golden_chart():
    c = calculate_natal_chart(GOLDEN["dob"], GOLDEN["tob"], GOLDEN["lat"], GOLDEN["lon"], GOLDEN["tz"])
    return ensure_dasha(c)


def test_simulator_returns_core_sections():
    chart = _golden_chart()
    out = compute_life_cycle_simulation(chart, horizon_years=10)
    assert "dasha_timeline" in out
    assert "transit_hits" in out
    assert "impact_areas" in out
    assert "top_windows" in out
    assert out["meta"]["horizon_years"] == 10
    assert "drishti_rules" in out["meta"]


def test_simulator_dasha_timeline_covers_horizon():
    chart = _golden_chart()
    out = compute_life_cycle_simulation(chart, horizon_years=10)
    segs = out["dasha_timeline"]
    assert len(segs) >= 3
    today = datetime.date.today()
    end = today + datetime.timedelta(days=int(10 * 365.25))
    for seg in segs:
        assert seg["mahadasha"] and seg["antardasha"]
        assert seg["focus_houses"]
        s = datetime.date.fromisoformat(seg["start"])
        e = datetime.date.fromisoformat(seg["end"])
        assert s <= e
        assert s >= today or e >= today
        assert s <= end


def test_simulator_transit_hits_and_drishti():
    chart = _golden_chart()
    out = compute_life_cycle_simulation(chart, horizon_years=10)
    hits = out["transit_hits"]
    assert len(hits) >= 4
    planets = {h["planet"] for h in hits}
    assert "Jupiter" in planets or "Saturn" in planets
    for h in hits:
        assert h["start"] <= h["end"]
        assert h["target"]


def test_transit_hits_are_not_full_horizon_spans():
    """Each hit must be a bounded sign transit, not the entire 10-year window."""
    chart = _golden_chart()
    out = compute_life_cycle_simulation(chart, horizon_years=10)
    horizon_days = int(10 * 365.25)
    for h in out["transit_hits"]:
        assert h["duration_days"] < horizon_days * 0.85, (
            f"{h['planet']} spans {h['duration_days']} days — likely scan bug"
        )


def test_simulator_impact_areas_include_drishti():
    chart = _golden_chart()
    out = compute_life_cycle_simulation(chart, horizon_years=10)
    areas = out["impact_areas"]
    assert len(areas) == 12
    assert all("planets_aspecting" in a for a in areas)
    assert all("strength" in a for a in areas)
    # At least one house should have aspecting planets in this chart
    assert any(a["planets_aspecting"] for a in areas)


def test_simulator_top_windows_ranked():
    chart = _golden_chart()
    out = compute_life_cycle_simulation(chart, horizon_years=10)
    tops = out["top_windows"]
    if len(tops) >= 2:
        assert tops[0]["score"] >= tops[1]["score"]
    for w in tops:
        assert w["overlap_days"] >= 14
        assert w["summary"]


def test_golden_chart_lagna():
    chart = _golden_chart()
    assert chart["ascendant"]["sign"] == "Aquarius"


def test_phase2_event_themes():
    chart = _golden_chart()
    out = compute_life_cycle_simulation(chart, horizon_years=10)
    themes = out["event_themes"]
    assert len(themes) == 6
    keys = {t["key"] for t in themes}
    assert "marriage" in keys and "career" in keys
    for t in themes:
        assert t["verdict"] in ("highly_active", "active", "moderate", "quiet")
        assert "d9_overlay" in t
        assert "natal_promise_score" in t
        assert "activation_score" in t
        assert "has_caution" in t


def test_phase2_narration():
    chart = _golden_chart()
    out = compute_life_cycle_simulation(chart, horizon_years=10)
    narr = out["narration"]
    assert narr["headline"]
    assert narr["method_note"]
    assert len(narr["theme_summaries"]) >= 1
    assert out["meta"]["phase"] == 3
    assert out["meta"]["navamsa_lagna"]


def test_theme_peaks_are_theme_specific():
    """Each theme peak should tie to that theme's houses/karakas — not one global window."""
    chart = _golden_chart()
    out = compute_life_cycle_simulation(chart, horizon_years=10)
    peaks = [t.get("peak_window") for t in out["event_themes"] if t.get("peak_window")]
    assert len(peaks) >= 3
    summaries = [p["summary"] for p in peaks]
    assert len(set(summaries)) > 1, "All themes must not share identical peak summaries"

    health = next(t for t in out["event_themes"] if t["key"] == "health")
    hpeak = health.get("peak_window")
    assert hpeak, "Health theme should have a peak"
    theme_h = set(hpeak.get("theme_houses") or [])
    assert theme_h & {6, 8, 12} or hpeak.get("signals", {}).get("lord_transit") or hpeak.get("type") == "pratyantar", (
        "Health peak must hit H6/H8/H12, lord transit, or theme PD"
    )

    marriage = next(t for t in out["event_themes"] if t["key"] == "marriage")
    mpeak = marriage.get("peak_window")
    if mpeak:
        assert (
            set(mpeak.get("theme_houses") or []) & {2, 7, 11}
            or mpeak.get("signals", {}).get("lord_transit")
            or mpeak.get("type") == "pratyantar"
        )


def test_phase3_pratyantar_and_sav():
    chart = _golden_chart()
    out = compute_life_cycle_simulation(chart, horizon_years=10)
    assert out["meta"]["phase"] == 3
    assert len(out.get("pratyantar_timeline") or []) >= 9
    pd = out["pratyantar_timeline"][0]
    assert pd["mahadasha"] and pd["antardasha"] and pd["pratyantar"]

    for t in out["event_themes"]:
        assert "sav" in t
        assert t["sav"]["average"] > 0
        assert t["sav"]["by_house"]
        assert "pratyantar_windows" in t

    # At least one theme should surface PD windows
    assert any(t.get("pratyantar_windows") for t in out["event_themes"])

    # Themes should not all collapse to the same verdict
    verdicts = {t["verdict"] for t in out["event_themes"]}
    assert len(verdicts) >= 2, f"Expected diverse verdicts, got {verdicts}"

    cur = out.get("current_period")
    assert cur
    if cur.get("pratyantar"):
        assert cur["pratyantar_start"] <= cur["pratyantar_end"]
