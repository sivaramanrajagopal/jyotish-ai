"""Career prediction — D10, 10 rules, profession tags, cross-repo validation."""

from __future__ import annotations

import csv
from pathlib import Path

from agents.career.d10 import build_dasamsa_from_natal, d1_longitude_to_d10
from agents.career_agent import compute_career_prediction, career_context_for_narrator
from agents.natal_agent import calculate_natal_chart

CHENNAI = {
    "dob": "1978-09-18",
    "tob": "17:35",
    "lat": 13.0827,
    "lon": 80.2707,
    "tz": "Asia/Kolkata",
}

# Birth data from Astro-birthchart-Database thesis exports
CROSS_REPO_NATIVES = [
    {
        "name": "Sivaraman R",
        "chart_id": 3,
        "dob": "1978-09-18",
        "tob": "17:35",
        "lat": 13.0827,
        "lon": 80.2707,
        "tz": "Asia/Kolkata",
        "expected_rules": 6,
        "expected_tenth_lord": "Mars",
        "expected_d10_lagna": "Virgo",
    },
    {
        "name": "Narendra Modi",
        "chart_id": 17,
        "dob": "1950-09-17",
        "tob": "11:00",
        "lat": 23.7757259,
        "lon": 72.6165643,
        "tz": "Asia/Kolkata",
        "expected_tenth_lord": "Sun",
        "expected_d10_lagna": "Cancer",
    },
    {
        "name": "Sundar Pichai",
        "chart_id": 15,
        "dob": "1972-06-10",
        "tob": "23:25",
        "lat": 9.9252007,
        "lon": 78.1197754,
        "tz": "Asia/Kolkata",
        "expected_rules": 2,
        "expected_tenth_lord": "Mars",
    },
]

TAMIL_TO_ENGLISH = {
    "Mesha": "Aries",
    "Rishaba": "Taurus",
    "Mithuna": "Gemini",
    "Kataka": "Cancer",
    "Simha": "Leo",
    "Kanni": "Virgo",
    "Thula": "Libra",
    "Vrischika": "Scorpio",
    "Dhanus": "Sagittarius",
    "Makara": "Capricorn",
    "Kumbha": "Aquarius",
    "Meena": "Pisces",
}

PDF10_KEYS = [
    ("1", "1_D1_planets_in_10th"),
    ("2", "2_D1_10th_lord_placement"),
    ("3", "3_D1_10th_lord_in_10th"),
    ("4", "4_D10_planets_in_10th"),
    ("5", "5_D10_10th_lord"),
    ("6", "6_D10_lagna_strength"),
    ("7", "7_Atmakaraka"),
    ("9", "9_Sun_Mars_Saturn_D10"),
    ("10", "10_D10_Kendra"),
]

BIRTHCHART_DB = Path(__file__).resolve().parents[3].parent / (
    "Documents/Astrology-Projects/Astro-birthchart-Database"
)


def _chart(native: dict | None = None):
    n = native or CHENNAI
    c = calculate_natal_chart(n["dob"], n["tob"], n["lat"], n["lon"], n["tz"])
    c["birth_data"] = {"dob": n["dob"], "timezone": n["tz"]}
    return c


def _load_pdf10_matrix() -> dict[int, dict]:
    path = BIRTHCHART_DB / "exports" / "pdf10_rules_matrix.csv"
    if not path.is_file():
        return {}
    out: dict[int, dict] = {}
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            cid = int(row["chart_id"])
            out[cid] = {rid: row[col] == "Yes" for rid, col in PDF10_KEYS}
    return out


def _load_thesis_d10_rows(chart_id: int) -> list[dict]:
    import json

    path = BIRTHCHART_DB / "exports" / "thesis_30_dump.json"
    if not path.is_file():
        return []
    data = json.loads(path.read_text())
    for case in data:
        if case.get("chart_id") == chart_id:
            return case.get("d10_rows") or []
    return []


def test_d10_longitude_deterministic():
    assert 0 <= d1_longitude_to_d10(0.0) < 360


def test_dasamsa_positions_shape():
    chart = _chart()
    asc, pos = build_dasamsa_from_natal(chart)
    assert "sign_index" in asc
    assert "Sun" in pos
    assert "house" in pos["Sun"]
    assert "degree_in_sign" in pos["Sun"]


def test_career_prediction_structure():
    out = compute_career_prediction(_chart())
    assert len(out["rules"]) == 10
    assert out["summary"]["rules_total"] == 10
    assert out["summary"]["tenth_lord"]
    assert out["summary"]["atmakaraka"]
    assert out["profession_tags"]
    assert out["dasamsa_positions"]
    assert out["dasamsa_ascendant"]
    assert "timing" in out


def test_career_narrator_context():
    ctx = career_context_for_narrator(_chart())
    assert "Career" in ctx
    assert "D1" in ctx or "10th lord" in ctx


def test_sivaraman_native_six_rules():
    """Native chart (Chennai 1978) — thesis viva documents 6/10 rules."""
    out = compute_career_prediction(_chart(CHENNAI))
    s = out["summary"]
    assert s["rules_matched"] == 6
    assert s["tenth_lord"] == "Mars"
    assert out["dasamsa_ascendant"]["sign"] == "Virgo"
    rules = {r["id"]: r["matched"] for r in out["rules"]}
    assert rules["4"] is True   # Moon in D10 10th
    assert rules["8"] is True   # career Dasa link in timeline
    assert rules["1"] is False  # no D1 planets in 10th


def test_cross_repo_pdf10_rules_match_thesis():
    """Rules 1–7, 9–10 vs pdf10_rules_matrix.csv (rule 8 differs by design)."""
    matrix = _load_pdf10_matrix()
    if not matrix:
        return  # skip when birthchart DB not on this machine

    for native in CROSS_REPO_NATIVES:
        cid = native.get("chart_id")
        if not cid or cid not in matrix:
            continue
        out = compute_career_prediction(_chart(native))
        rules = {r["id"]: r["matched"] for r in out["rules"]}
        expected = matrix[cid]
        for rid, col in PDF10_KEYS:
            assert rules[rid] == expected[rid], (
                f"{native['name']} R{rid}: got {rules[rid]}, thesis {expected[rid]}"
            )
        if "expected_rules" in native:
            assert out["summary"]["rules_matched"] == native["expected_rules"], native["name"]


def test_cross_repo_d10_placements_match_thesis():
    """D10 whole-sign placements vs thesis_30_dump.json."""
    for native in CROSS_REPO_NATIVES:
        cid = native.get("chart_id")
        if not cid:
            continue
        rows = _load_thesis_d10_rows(cid)
        if not rows:
            continue
        chart = _chart(native)
        _, pos = build_dasamsa_from_natal(chart)
        for row in rows:
            planet = row["planet"]
            if planet not in pos:
                continue
            # Thesis dump used true node; this engine uses mean node.
            if planet in ("Rahu", "Ketu"):
                continue
            exp_sign = TAMIL_TO_ENGLISH.get(row["rasi"], row["rasi"])
            assert pos[planet]["sign"] == exp_sign, (
                f"{native['name']} {planet} sign: {pos[planet]['sign']} vs {exp_sign}"
            )
            assert pos[planet]["house"] == row["house"], (
                f"{native['name']} {planet} house: H{pos[planet]['house']} vs H{row['house']}"
            )
        if native.get("expected_d10_lagna"):
            assert chart and pos  # placate linter
            asc, _ = build_dasamsa_from_natal(chart)
            assert asc["sign"] == native["expected_d10_lagna"]


def test_d10_rahu_ketu_derived_from_d1_mean_node():
    chart = _chart(CHENNAI)
    _, pos = build_dasamsa_from_natal(chart)
    pp = chart["planet_positions"]
    rahu_d1 = pp["Rahu"]["longitude"]
    ketu_d1 = pp["Ketu"]["longitude"]
    assert abs(((ketu_d1 - rahu_d1) % 360) - 180) < 1e-4
    rahu_d10 = d1_longitude_to_d10(rahu_d1)
    ketu_d10 = d1_longitude_to_d10(ketu_d1)
    assert pos["Rahu"]["sign_index"] == int(rahu_d10 // 30) % 12
    assert pos["Ketu"]["sign_index"] == int(ketu_d10 // 30) % 12
    assert pos["Rahu"]["sign"] == "Gemini"
    assert pos["Ketu"]["sign"] == "Sagittarius"
