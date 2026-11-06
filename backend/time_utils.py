"""Calendar "today" for the app. The server clock may run in UTC; the app's day is local."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

APP_TZ = "Asia/Kolkata"


def today_in(tz: str | None = None) -> date:
    """Today's date in an IANA timezone (defaults to IST)."""
    try:
        zone = ZoneInfo(tz or APP_TZ)
    except Exception:
        zone = ZoneInfo(APP_TZ)
    return datetime.now(zone).date()


def today_ist() -> date:
    return today_in(APP_TZ)
