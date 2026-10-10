"""A small iCalendar feed: one all-day line and Rahu Kalam. Horai stay off the calendar."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from agents.panchangam_agent import LOCATIONS, calculate_panchangam
from agents.tara_engine import compute_tara_balam


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def _utc_stamp(iso: str) -> str:
    moment = datetime.fromisoformat(iso)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=ZoneInfo("UTC"))
    return moment.astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")


def _local_clock(iso: str, tz: ZoneInfo) -> str:
    moment = datetime.fromisoformat(iso)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=ZoneInfo("UTC"))
    return moment.astimezone(tz).strftime("%H:%M")


def _day_summary(panch: dict, natal_nak: int | None) -> str:
    tithi = f"{panch.get('tithi_paksha') or ''} {panch.get('tithi_name') or ''}".strip()
    pada = panch.get("nakshatra_pada")
    star = panch.get("nakshatra_name") or ""
    if pada:
        star = f"{star} {pada}".strip()
    parts = [panch.get("vaaram_name") or "", tithi, star]
    if natal_nak is not None and panch.get("nakshatra_index"):
        today_nak = int(panch["nakshatra_index"]) - 1
        tara = compute_tara_balam(natal_nak, today_nak)
        if tara.get("name"):
            parts.append(f"Tara {tara['name']}")
    return " · ".join(part for part in parts if part)


def build_panchangam_ics(
    location: str,
    days: int = 30,
    natal_nak: int | None = None,
    start: date | None = None,
) -> str:
    """Publish `days` of all-day lines and Rahu Kalam blocks for one city."""
    if location not in LOCATIONS:
        raise ValueError(f"Unknown location '{location}'.")
    tz_name = LOCATIONS[location]["tz"]
    tz = ZoneInfo(tz_name)
    first = start or datetime.now(tz).date()
    span = max(1, min(int(days), 60))
    now = datetime.now(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Parashara Jyotish//Panchangam//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:Panchangam {location}",
        f"X-WR-TIMEZONE:{tz_name}",
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
        "X-PUBLISHED-TTL:PT12H",
    ]
    for offset in range(span):
        day = first + timedelta(days=offset)
        panch = calculate_panchangam(day.isoformat(), location)
        summary = _day_summary(panch, natal_nak)
        sunrise = _local_clock(panch["sunrise"], tz) if panch.get("sunrise") else ""
        sunset = _local_clock(panch["sunset"], tz) if panch.get("sunset") else ""
        detail = " · ".join(
            bit for bit in (
                f"Sunrise {sunrise}" if sunrise else "",
                f"Sunset {sunset}" if sunset else "",
            ) if bit
        )
        next_day = day + timedelta(days=1)
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:panchangam-{location}-{day.isoformat()}@jyotish",
            f"DTSTAMP:{now}",
            f"DTSTART;VALUE=DATE:{day.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{next_day.strftime('%Y%m%d')}",
            f"SUMMARY:{_esc(summary)}",
            f"DESCRIPTION:{_esc(detail)}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ])
        if panch.get("rahu_kalam_start") and panch.get("rahu_kalam_end"):
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:rahu-{location}-{day.isoformat()}@jyotish",
                f"DTSTAMP:{now}",
                f"DTSTART:{_utc_stamp(panch['rahu_kalam_start'])}",
                f"DTEND:{_utc_stamp(panch['rahu_kalam_end'])}",
                "SUMMARY:Rahu Kalam",
                "DESCRIPTION:Busy. A new start waits until this window ends.",
                "TRANSP:OPAQUE",
                "BEGIN:VALARM",
                "TRIGGER:-PT10M",
                "ACTION:DISPLAY",
                "DESCRIPTION:Rahu Kalam begins",
                "END:VALARM",
                "END:VEVENT",
            ])
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
