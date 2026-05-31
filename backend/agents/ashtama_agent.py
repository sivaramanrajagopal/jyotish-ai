"""
ashtama_agent.py
================
FastAPI router for Chandra Ashtama + Tara Balam + Chandrabalam endpoints.

Endpoints:
  GET  /personal-panchangam/today/{user_id}
       Returns today's Tara, Ashtama, Chandrabalam for a registered user.
       Requires the user to have a natal chart in natal_charts table with
       moon_nakshatra_index and moon_rasi_index populated.

  GET  /personal-panchangam/anonymous
       Same, but caller passes natal_nak_index + natal_rasi_index directly.
       Useful before auth is wired up (frontend passes chart data).

  PUT  /personal-panchangam/location/{user_id}
       Store/update the user's current location for Panchangam purposes.

Register in main.py:
    from agents.ashtama_agent import router as ashtama_router
    app.include_router(ashtama_router)
"""

import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from agents.tara_engine import compute_all, NAKSHATRAS, SIGNS

router = APIRouter(prefix="/personal-panchangam", tags=["Personal Panchangam"])


# ── Supabase (optional — graceful degradation if not configured) ──────────────

try:
    from supabase_client import get_supabase
    _SB = True
except Exception:
    _SB = False


def _get_natal_indices(user_id: str) -> tuple[int, int, str]:
    """
    Fetch moon_nakshatra_index, moon_rasi_index, and timezone from Supabase.
    Returns (nak_index, rasi_index, timezone).
    Raises HTTPException if user/chart not found.
    """
    if not _SB:
        raise HTTPException(status_code=503, detail="Database not configured.")
    try:
        sb = get_supabase()
        # Get natal chart
        result = (
            sb.table("natal_charts")
            .select("moon_nakshatra_index, moon_rasi_index")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        if not result or not result.data:
            raise HTTPException(
                status_code=404,
                detail=f"No natal chart found for user {user_id}. "
                       "Calculate a natal chart first."
            )
        nak_idx  = result.data.get("moon_nakshatra_index")
        rasi_idx = result.data.get("moon_rasi_index")
        if nak_idx is None or rasi_idx is None:
            raise HTTPException(
                status_code=422,
                detail="Natal chart is missing moon_nakshatra_index / moon_rasi_index. "
                       "Recalculate the natal chart."
            )

        # Get user's current location timezone (fallback to IST)
        loc = (
            sb.table("user_locations")
            .select("timezone")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        tz = (loc.data or {}).get("timezone", "Asia/Kolkata") if loc else "Asia/Kolkata"

        return int(nak_idx), int(rasi_idx), tz

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")


def _serialize(result: dict) -> dict:
    """Convert datetime objects to ISO strings for JSON serialisation."""
    out = dict(result)
    ashtama = dict(out.get("chandra_ashtama", {}))
    for key in ("start", "end", "next_ashtama_start"):
        v = ashtama.get(key)
        if v and hasattr(v, "isoformat"):
            ashtama[key] = v.isoformat()
    out["chandra_ashtama"] = ashtama
    return out


def _store_result(user_id: str, result: dict, target_date: datetime.date) -> None:
    """Persist computed daily panchangam to Supabase (best-effort)."""
    if not _SB:
        return
    try:
        sb = get_supabase()
        ashtama = result["chandra_ashtama"]
        tara    = result["tara"]
        cb      = result["chandrabalam"]

        def _iso(v):
            return v.isoformat() if v and hasattr(v, "isoformat") else None

        row = {
            "user_id":             user_id,
            "date":                target_date.isoformat(),
            "tara_position":       tara["position"],
            "tara_name":           tara["name"],
            "tara_nature":         tara["nature"],
            "tara_colour":         tara["colour"],
            "tara_meaning":        tara["meaning"],
            "is_chandra_ashtama":  ashtama["is_active"],
            "ashtama_start":       _iso(ashtama.get("start")),
            "ashtama_end":         _iso(ashtama.get("end")),
            "next_ashtama_date":   _iso(ashtama.get("next_ashtama_start")),
            "chandrabalam_good":   cb["good"],
            "moon_house_from_natal": cb["house_from_natal"],
            "natal_moon_nak":      result["natal_nak_name"],
            "natal_moon_rasi":     result["natal_rasi_name"],
            "today_moon_sign":     result["today_moon_rasi"],
            "today_moon_nak":      result["today_moon_nak"],
        }
        sb.table("user_daily_panchangam").upsert(row).execute()
    except Exception as e:
        print(f"[ashtama_agent] store error: {e}")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/today/{user_id}")
def personal_panchangam_today(
    user_id: str,
    date: Optional[str] = Query(None, description="YYYY-MM-DD, defaults to today"),
):
    """
    Get today's personal Panchangam for a registered user.
    Requires natal chart with moon_nakshatra_index + moon_rasi_index in DB.
    """
    nak_idx, rasi_idx, timezone = _get_natal_indices(user_id)

    target_date = (
        datetime.date.fromisoformat(date) if date else datetime.date.today()
    )
    # Use noon local time as the reference point for the day
    from zoneinfo import ZoneInfo
    dt = datetime.datetime(
        target_date.year, target_date.month, target_date.day,
        12, 0, 0, tzinfo=ZoneInfo(timezone)
    )

    result = compute_all(nak_idx, rasi_idx, dt, timezone)
    _store_result(user_id, result, target_date)
    return _serialize(result)


@router.get("/anonymous")
def personal_panchangam_anonymous(
    natal_nak_index:  int = Query(..., ge=0, le=26,
                                  description="Natal Moon nakshatra index 0–26"),
    natal_rasi_index: int = Query(..., ge=0, le=11,
                                  description="Natal Moon rasi index 0–11"),
    timezone: str = Query("Asia/Kolkata", description="IANA timezone"),
    date: Optional[str] = Query(None, description="YYYY-MM-DD, defaults to today"),
):
    """
    Compute personal Panchangam without a user account.
    Pass natal_nak_index and natal_rasi_index directly (from the natal chart response).

    Use this endpoint until Supabase Auth is wired up.
    """
    target_date = (
        datetime.date.fromisoformat(date) if date else datetime.date.today()
    )
    from zoneinfo import ZoneInfo
    dt = datetime.datetime(
        target_date.year, target_date.month, target_date.day,
        12, 0, 0, tzinfo=ZoneInfo(timezone)
    )
    result = compute_all(natal_nak_index, natal_rasi_index, dt, timezone)
    return _serialize(result)


class LocationUpdate(BaseModel):
    city:     str
    lat:      float
    lon:      float
    timezone: str = "Asia/Kolkata"


@router.put("/location/{user_id}")
def update_user_location(user_id: str, body: LocationUpdate):
    """
    Store or update the user's current location for Panchangam calculation.
    """
    if not _SB:
        raise HTTPException(status_code=503, detail="Database not configured.")
    try:
        sb = get_supabase()
        sb.table("user_locations").upsert({
            "user_id":  user_id,
            "city":     body.city,
            "lat":      body.lat,
            "lon":      body.lon,
            "timezone": body.timezone,
        }).execute()
        return {"status": "ok", "user_id": user_id, "city": body.city}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Scheduler job (called by APScheduler in main.py) ─────────────────────────

def daily_personal_panchangam_job() -> None:
    """
    Run at 04:30 AM IST daily.
    Computes today's personal Panchangam for ALL users who have natal charts
    with moon indices populated, and stores results in user_daily_panchangam.
    """
    if not _SB:
        print("[ashtama_agent] Supabase not configured — skipping daily job.")
        return

    from zoneinfo import ZoneInfo
    today = datetime.date.today()
    tz    = ZoneInfo("Asia/Kolkata")
    dt    = datetime.datetime(today.year, today.month, today.day, 12, 0, 0, tzinfo=tz)

    try:
        sb = get_supabase()
        charts = (
            sb.table("natal_charts")
            .select("user_id, moon_nakshatra_index, moon_rasi_index")
            .not_.is_("moon_nakshatra_index", "null")
            .execute()
        )
        if not charts or not charts.data:
            print("[ashtama_agent] No natal charts with moon indices found.")
            return

        count = 0
        for row in charts.data:
            uid      = row["user_id"]
            nak_idx  = row["moon_nakshatra_index"]
            rasi_idx = row["moon_rasi_index"]
            if uid is None:
                continue
            try:
                # Get user's stored timezone
                loc = (
                    sb.table("user_locations")
                    .select("timezone")
                    .eq("user_id", uid)
                    .maybe_single()
                    .execute()
                )
                user_tz = (loc.data or {}).get("timezone", "Asia/Kolkata") if loc else "Asia/Kolkata"
                user_dt = datetime.datetime(today.year, today.month, today.day,
                                            12, 0, 0, tzinfo=ZoneInfo(user_tz))
                result = compute_all(int(nak_idx), int(rasi_idx), user_dt, user_tz)
                _store_result(uid, result, today)
                count += 1
            except Exception as e:
                print(f"[ashtama_agent] job error for {uid}: {e}")

        print(f"[ashtama_agent] daily job complete — {count} users processed.")

    except Exception as e:
        print(f"[ashtama_agent] job fatal error: {e}")
