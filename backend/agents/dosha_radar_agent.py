"""
dosha_radar_agent.py — Dosha Radar: Tamil blueprint + afflictions + Pushkara + transit scan.
"""

from __future__ import annotations

import datetime

from agents.dosha_radar.afflictions import check_combustion, check_critical_obstruction, check_gandanta
from agents.dosha_radar.obstruction import (
    build_obstruction_profile,
    compute_live_transit_status,
    scan_all_dosha_transits,
)
from agents.dosha_radar.pushkara import check_pushkara, scan_all_pushkara_transits
from agents.tamil_dosha_agent import compute_tamil_doshas

DISCLAIMER_EN = (
    "For informational and timing-awareness purposes only. Not a substitute for "
    "professional advice. Obstruction doshas indicate caution windows — Pushkara "
    "zones may soften outcomes."
)
DISCLAIMER_TA = (
    "தகவல் மற்றும் கால விழிப்புணர்வுக்காக மட்டும். தொழில்முறை ஆலோசனைக்கு மாற்று அல்ல. "
    "தடை தோஷங்கள் கவன காலங்களைக் குறிக்கும் — புஷ்கரம் மென்மையாக்கலாம்."
)

_SEVERITY_RANK = {
    "none": 0,
    "soonya": 1,
    "mild": 2,
    "mild_divine": 3,
    "chandrashtama": 4,
    "mudakku": 4,
    "red_zone": 5,
    "critical": 6,
    "critical_divine": 7,
}


def _transit_ref_dt(natal_chart: dict) -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _build_natal_afflictions(natal_chart: dict, soonya_rasis: list[int]) -> dict:
    pp = natal_chart.get("planet_positions") or {}
    sun_lon = (pp.get("Sun") or {}).get("longitude", 0.0)
    out: dict[str, dict] = {}

    for pname, pdata in pp.items():
        lon = float(pdata.get("longitude", 0))
        retro = bool(pdata.get("retrograde", False))
        sign_idx = pdata.get("sign_index")
        if sign_idx is None:
            sign_idx = int(lon / 30) % 12

        combust = (
            check_combustion(sun_lon, lon, pname, retro)
            if pname != "Sun"
            else {"combust": False, "deep": False, "orb": 0.0, "cross_sign": False}
        )
        gandanta = check_gandanta(lon)
        pushkara = check_pushkara(lon)
        crit = check_critical_obstruction(
            {"sign_idx": sign_idx, "combust": combust, "gandanta": gandanta, "pushkara": pushkara},
            soonya_rasis,
        )
        out[pname] = {
            "sign": pdata.get("sign"),
            "house": pdata.get("house"),
            "combust": combust,
            "gandanta": gandanta,
            "pushkara": pushkara,
            "in_soonya": sign_idx in soonya_rasis,
            "critical_obstruction": crit,
        }
    return out


def _active_alerts(transit: dict) -> list[dict]:
    alerts: list[dict] = []
    for pname, d in (transit.get("planets") or {}).items():
        crit = d.get("critical_obstruction") or {}
        sev = crit.get("severity", "none")
        if sev in ("critical", "critical_divine", "mild", "mild_divine"):
            alerts.append({
                "planet": pname,
                "severity": sev,
                "sign": d.get("sign"),
                "note_en": crit.get("visha_gati_note", ""),
                "note_ta": crit.get("visha_gati_note_ta", ""),
                "has_divine_protection": crit.get("has_divine_protection", False),
            })
        if d.get("in_chandrashtama"):
            alerts.append({
                "planet": pname,
                "severity": "chandrashtama",
                "sign": d.get("sign"),
                "note_en": "Chandrashtama — Moon in 8th from natal Moon sign.",
                "note_ta": "சந்திராஷ்டமம் — ஜன்ம சந்திரத்தின் 8ம் ராசியில் சந்திரன்.",
                "has_divine_protection": False,
            })
        if d.get("red_zone"):
            alerts.append({
                "planet": pname,
                "severity": "red_zone",
                "sign": d.get("sign"),
                "note_en": f"Red zone transit: {d['red_zone']} ({d.get('nak_name', '')})",
                "note_ta": f"சிவப்பு மண்டலம்: {d['red_zone']}",
                "has_divine_protection": d.get("red_zone") == "Transformational",
            })
        if d.get("in_mudakku"):
            alerts.append({
                "planet": pname,
                "severity": "mudakku",
                "sign": d.get("sign"),
                "note_en": "Mudakku Rasi (22nd Drekkana) — blocked sign transit.",
                "note_ta": "முடக்கு ராசி — தடைபட்ட ராசி கோசாரம்.",
                "has_divine_protection": False,
            })
        if (
            d.get("in_soonya")
            and sev == "none"
            and not d.get("red_zone")
            and not d.get("in_chandrashtama")
            and not d.get("in_mudakku")
        ):
            alerts.append({
                "planet": pname,
                "severity": "soonya",
                "sign": d.get("sign"),
                "note_en": f"Transiting Soonya Rasi ({d.get('sign')}) — results may be weakened or erratic.",
                "note_ta": f"சூன்ய ராசி கோசாரம் ({d.get('sign')}) — பலன்கள் மெதுவாக அல்லது நிலையற்றதாக.",
                "has_divine_protection": bool(d.get("pushkara", {}).get("pushkara")),
            })
    alerts.sort(key=lambda a: _SEVERITY_RANK.get(a.get("severity", "none"), 0), reverse=True)
    return alerts


def _transit_highlights(transit: dict) -> list[dict]:
    """Compact list of planets with any transit flag — for hero / mobile cards."""
    highlights: list[dict] = []
    for pname, d in (transit.get("planets") or {}).items():
        flags: list[str] = []
        if d.get("in_soonya"):
            flags.append("Soonya")
        if d.get("in_chandrashtama"):
            flags.append("Chandrashtama")
        if d.get("in_mudakku"):
            flags.append("Mudakku")
        if d.get("red_zone"):
            flags.append(d["red_zone"])
        if d.get("pushkara", {}).get("pushkara"):
            flags.append("Pushkara")
        crit = (d.get("critical_obstruction") or {}).get("severity", "none")
        if crit not in ("none", ""):
            flags.append(crit.replace("_", " "))
        if not flags:
            continue
        highlights.append({
            "planet": pname,
            "sign": d.get("sign"),
            "house_num": d.get("house_num"),
            "flags": flags,
            "nak_name": d.get("nak_name"),
            "has_divine_protection": (
                d.get("red_zone") == "Transformational"
                or bool(d.get("pushkara", {}).get("pushkara"))
                or bool((d.get("critical_obstruction") or {}).get("has_divine_protection"))
            ),
        })
    return highlights


def compute_dosha_radar_analysis(natal_chart: dict) -> dict:
    tamil = compute_tamil_doshas(natal_chart)
    profile = build_obstruction_profile(natal_chart, tamil)
    soonya_rasis = profile["soonya_rasis"]

    ref_dt = _transit_ref_dt(natal_chart)
    natal_afflictions = _build_natal_afflictions(natal_chart, soonya_rasis)
    transit = compute_live_transit_status(natal_chart, profile, ref_dt)
    forecast = scan_all_dosha_transits(profile, ref_dt, days_ahead=90)
    pushkara_transits = scan_all_pushkara_transits(reference_dt=ref_dt, days_ahead=180)

    pushkara_natal = [
        {"planet": p, "pushkara": d["pushkara"].get("pushkara"), "zone": d["pushkara"].get("zone", "")}
        for p, d in natal_afflictions.items()
        if d["pushkara"].get("pushkara")
    ]

    divine_count = sum(
        1 for d in natal_afflictions.values()
        if d.get("critical_obstruction", {}).get("has_divine_protection")
    )
    active = _active_alerts(transit)
    highlights = _transit_highlights(transit)
    top_sev = active[0]["severity"] if active else "clear"

    return {
        "disclaimer": {"en": DISCLAIMER_EN, "ta": DISCLAIMER_TA},
        "summary": {
            "transit_date": transit["transit_date"],
            "overall_status": top_sev,
            "active_alert_count": len(active),
            "natal_pushkara_count": len(pushkara_natal),
            "divine_protection_natal": divine_count,
            "soonya_signs": profile["soonya_signs"],
            "chandrashtama_sign": profile["chandrashtama_sign"],
            "mudakku_sign": profile["mudakku"]["sign_name"],
            "vadhai_nakshatra": profile["vadhai_nak_name"],
            "vainasikam_nakshatra": profile["vainasikam_nak_name"],
            "forecast_horizon_days": forecast["days_ahead"],
            "transit_highlight_count": len(highlights),
        },
        "tamil_blueprint": tamil,
        "obstruction_profile": profile,
        "natal_afflictions": natal_afflictions,
        "pushkara_natal": pushkara_natal,
        "transit_status": transit,
        "active_alerts": active,
        "transit_highlights": highlights,
        "forecast": forecast,
        "pushkara_transits": pushkara_transits,
    }


def dosha_radar_context_for_narrator(natal_chart: dict) -> str:
    try:
        d = compute_dosha_radar_analysis(natal_chart)
    except Exception:
        return ""

    prof = d["obstruction_profile"]
    lines = [
        "=== DOSHA RADAR (obstruction + Pushkara — use for transit caution & divine protection) ===",
        f"Soonya (dagdha) signs: {', '.join(prof['soonya_signs']) or 'none'}",
        f"Chandrashtama sign: {prof['chandrashtama_sign']} ({prof['chandrashtama_english']})",
        f"Mudakku (22nd Drekkana): {prof['mudakku']['sign_name']} H{prof['mudakku_house']}",
        f"Vadhai nakshatra: {prof['vadhai_nak_name']} | Vainasikam: {prof['vainasikam_nak_name']}",
        "",
        "NATAL PUSHKARA NAVAMSA:",
    ]
    for pk in d["pushkara_natal"]:
        lines.append(f"  {pk['planet']}: {pk['zone']}")

    lines.append("")
    lines.append(f"ACTIVE TRANSIT ALERTS (as of {d['summary']['transit_date']}):")
    if d["active_alerts"]:
        for a in d["active_alerts"][:12]:
            divine = " [DIVINE PROTECTION]" if a.get("has_divine_protection") else ""
            lines.append(f"  - {a['planet']} ({a['severity']}): {a['note_en']}{divine}")
    else:
        lines.append("  None critical right now.")

    fc = d["forecast"]
    lines.append("")
    lines.append("UPCOMING 90-DAY WINDOWS (next 5 each):")
    for w in fc["chandrashtama_windows"][:3]:
        lines.append(f"  Chandrashtama: {w['start_date']} → {w['end_date']} ({w['duration_days']}d)")
    for e in fc["red_zone_entries"][:3]:
        tag = "Transformational/Pushkara" if e.get("has_pushkara") else e["type"]
        lines.append(f"  {e['planet']} → {tag} ({e['nak_name']}) on {e['entry_date']}")
    for c in fc["critical_windows"][:2]:
        divine = " + Pushkara" if c.get("has_divine") else ""
        lines.append(f"  {c['planet']} critical in Soonya {c['soonya_sign']} ({c['affliction_type']}){divine} on {c['date']}")

    lines.extend([
        "",
        "DOSHA RADAR RULES FOR AI:",
        "- Mention Pushkara Navamsa as Divine Protection when active (Visha→Amrita in red zones).",
        "- Distinguish natal blueprint (Tamil doshas) from live transit scan.",
        "- Chandrashtama = Moon in 8th from natal Moon sign; Mudakku = 22nd Drekkana blocked sign.",
        "- Practical timing caution only — no fear-mongering or guaranteed outcomes.",
        "=== END DOSHA RADAR ===",
    ])
    return "\n".join(lines)
