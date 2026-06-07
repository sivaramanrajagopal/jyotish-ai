"""
sky_today_agent.py — compact “cosmos strip” payload for the app header.
Universal: date, vaaram, tithi, Moon/Sun rasi, retrogrades, kalam alerts.
Personal (optional): Tara Balam, Moon house from natal ascendant, Chandra Ashtama.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

import ephemeris as swe

from agents.panchangam_agent import LOCATIONS, calculate_panchangam
from agents.natal_agent import (
    PLANETS,
    SIGNS,
    _is_retrograde,
    _lon_to_sign,
    _to_jd,
)
from agents.tara_engine import compute_all

SIGN_SHORT = {
    "Aries": "Mesha", "Taurus": "Rishaba", "Gemini": "Mithuna",
    "Cancer": "Kataka", "Leo": "Simha", "Virgo": "Kanni",
    "Libra": "Thula", "Scorpio": "Vrischika", "Sagittarius": "Dhanus",
    "Capricorn": "Makara", "Aquarius": "Kumbha", "Pisces": "Meena",
}


def _resolve_location(name: str, lat: float | None = None, lon: float | None = None) -> str:
    """Match user place string or coordinates to a known LOCATIONS key."""
    from location_utils import resolve_panchangam_location
    return resolve_panchangam_location(name, lat=lat, lon=lon)


def _fmt_time_short(iso: Optional[str], tz: ZoneInfo) -> Optional[str]:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt.astimezone(tz).strftime("%-I:%M %p")
    except Exception:
        return None


def _is_between(now: datetime, start_iso: Optional[str], end_iso: Optional[str]) -> bool:
    if not start_iso or not end_iso:
        return False
    try:
        s = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        e = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        if s.tzinfo is None:
            s = s.replace(tzinfo=now.tzinfo)
        if e.tzinfo is None:
            e = e.replace(tzinfo=now.tzinfo)
        return s <= now <= e
    except Exception:
        return False


def _starts_within(now: datetime, start_iso: Optional[str], minutes: int = 30) -> bool:
    if not start_iso:
        return False
    try:
        s = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        if s.tzinfo is None:
            s = s.replace(tzinfo=now.tzinfo)
        return now < s <= now + timedelta(minutes=minutes)
    except Exception:
        return False


def _planet_signs_now(jd: float) -> dict[str, dict]:
    """Sidereal sign + retrograde for grahas at jd."""
    out: dict[str, dict] = {}
    for name, pid in PLANETS.items():
        xx, _ = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
        sid_lon = xx[0] % 360
        sign, _ = _lon_to_sign(sid_lon)
        retro = _is_retrograde(pid, jd) if name not in ("Sun", "Moon") else False
        if name == "Rahu":
            retro = True
        out[name] = {
            "sign": sign,
            "sign_short": SIGN_SHORT.get(sign, sign),
            "sign_index": SIGNS.index(sign),
            "retrograde": retro,
        }
    return out


def _moon_house_from_asc(moon_sign_idx: int, asc_sign_idx: int) -> int:
    return (moon_sign_idx - asc_sign_idx + 12) % 12 + 1


def build_sky_today(
    location: str = "Chennai",
    moon_nak_index: Optional[int] = None,
    moon_rasi_index: Optional[int] = None,
    natal_asc_sign_index: Optional[int] = None,
) -> dict[str, Any]:
    loc_key = _resolve_location(location)
    loc = LOCATIONS[loc_key]
    tz = ZoneInfo(loc["tz"])
    now = datetime.now(tz)
    today_str = now.date().isoformat()

    panch = calculate_panchangam(today_str, loc_key)
    jd = _to_jd(now)
    planets = _planet_signs_now(jd)

    moon = planets["Moon"]
    sun = planets["Sun"]
    retro = [
        p for p, d in planets.items()
        if d["retrograde"] and p not in ("Rahu", "Ketu")
    ]
    retro_short = [f"{p[:2]} ℞" for p in retro]  # Sa ℞, Me ℞

    rahu_start = panch.get("rahu_kalam_start")
    rahu_end = panch.get("rahu_kalam_end")
    rahu_active = _is_between(now, rahu_start, rahu_end)
    rahu_soon = _starts_within(now, rahu_start)

    date_label = now.strftime("%a %-d %b")

    alert: Optional[dict[str, Any]] = None
    if rahu_active:
        alert = {
            "type": "rahu_kalam",
            "severity": "warning",
            "message": "Rahu Kalam active now",
            "until": _fmt_time_short(rahu_end, tz),
        }
    elif rahu_soon:
        alert = {
            "type": "rahu_kalam",
            "severity": "info",
            "message": f"Rahu Kalam starts {_fmt_time_short(rahu_start, tz) or 'soon'}",
            "until": None,
        }

    personal: Optional[dict[str, Any]] = None
    if moon_nak_index is not None and moon_rasi_index is not None:
        pp = compute_all(int(moon_nak_index), int(moon_rasi_index), now, loc["tz"])
        tara = pp.get("tara", {})
        ashtama = pp.get("chandra_ashtama", {})

        if ashtama.get("is_active") and not alert:
            alert = {
                "type": "chandra_ashtama",
                "severity": "warning",
                "message": "Chandra Ashtama active",
                "until": _fmt_time_short(ashtama.get("end"), tz),
            }

        moon_house = None
        if natal_asc_sign_index is not None:
            moon_house = _moon_house_from_asc(
                moon["sign_index"], int(natal_asc_sign_index)
            )

        personal = {
            "tara_name": tara.get("name"),
            "tara_nature": tara.get("nature"),
            "tara_favourable": tara.get("nature") == "benefic",
            "moon_house": moon_house,
            "ashtama_active": bool(ashtama.get("is_active")),
        }

    return {
        "date": today_str,
        "date_label": date_label,
        "location": loc_key,
        "timezone": loc["tz"],
        "vaaram": panch.get("vaaram_name"),
        "tithi": f"{panch.get('tithi_paksha', '')} {panch.get('tithi_name', '')}".strip(),
        "nakshatra": panch.get("nakshatra_name"),
        "moon_sign": moon["sign"],
        "moon_sign_short": moon["sign_short"],
        "sun_sign": sun["sign"],
        "sun_sign_short": sun["sign_short"],
        "retrograde": retro,
        "retrograde_short": retro_short,
        "rahu_kalam": {
            "start": rahu_start,
            "end": rahu_end,
            "active": rahu_active,
            "soon": rahu_soon,
        },
        "alert": alert,
        "personal": personal,
        "calculated_at": now.isoformat(),
    }
