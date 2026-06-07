"""
admin_router.py — owner dashboard API (reads Supabase analytics views).
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from admin_auth import require_admin
from auth import AuthUser
from rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

try:
    from supabase_client import get_supabase
    _SB = True
except Exception:
    _SB = False


def _table_count(table: str) -> int:
    sb = get_supabase()
    res = sb.table(table).select("*", count="exact").limit(0).execute()
    return res.count or 0


def _query_view(
    view: str,
    select: str = "*",
    order_col: Optional[str] = None,
    desc: bool = True,
    limit: Optional[int] = None,
) -> list[dict[str, Any]]:
    sb = get_supabase()
    q = sb.table(view).select(select)
    if order_col:
        q = q.order(order_col, desc=desc)
    if limit:
        q = q.limit(limit)
    res = q.execute()
    return res.data or []


def _users_fallback(limit: int) -> list[dict[str, Any]]:
    sb = get_supabase()
    users = (
        sb.table("users")
        .select("id, email, name, created_at, subscription_tier")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    ).data or []
    charts = {
        row["user_id"]: row
        for row in (
            sb.table("natal_charts")
            .select("user_id, sun_sign, moon_sign, ascendant, calculated_at, birth_form, chart_data")
            .execute()
        ).data or []
    }
    out = []
    for u in users:
        nc = charts.get(u["id"], {})
        bf = nc.get("birth_form") or {}
        out.append({
            "email": u.get("email"),
            "name": u.get("name"),
            "registered_at": u.get("created_at"),
            "subscription_tier": u.get("subscription_tier"),
            "has_chart": bool(nc),
            "has_full_chart": nc.get("chart_data") is not None,
            "sun_sign": nc.get("sun_sign"),
            "moon_sign": nc.get("moon_sign"),
            "ascendant": nc.get("ascendant"),
            "birth_place": bf.get("place_of_birth"),
            "chart_saved_at": nc.get("calculated_at"),
            "last_sign_in_at": None,
        })
    return out


@router.get("/overview")
@limiter.limit("30/minute")
def admin_overview(request: Request, _admin: AuthUser = Depends(require_admin)):
    if not _SB:
        raise HTTPException(status_code=503, detail="Database not configured.")

    today = date.today().isoformat()
    try:
        total_users = _table_count("users")
        total_charts = _table_count("natal_charts")
        sb = get_supabase()
        full_charts = (
            sb.table("natal_charts")
            .select("*", count="exact")
            .not_.is_("chart_data", "null")
            .limit(0)
            .execute()
        ).count or 0
        locations = _table_count("user_locations")
        ai_today = (
            sb.table("ai_usage")
            .select("*", count="exact")
            .eq("usage_date", today)
            .limit(0)
            .execute()
        ).count or 0
        ai_calls = (
            sb.table("ai_usage")
            .select("chat_count, forecast_count")
            .eq("usage_date", today)
            .execute()
        ).data or []
        chat_today = sum(r.get("chat_count") or 0 for r in ai_calls)
        forecast_today = sum(r.get("forecast_count") or 0 for r in ai_calls)
    except Exception as exc:
        logger.exception("admin overview failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not load overview.")

    return {
        "total_users": total_users,
        "total_charts": total_charts,
        "full_charts": full_charts,
        "users_with_location": locations,
        "ai_users_today": ai_today,
        "chat_calls_today": chat_today,
        "forecast_calls_today": forecast_today,
        "as_of": today,
    }


@router.get("/users")
@limiter.limit("30/minute")
def admin_users(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    _admin: AuthUser = Depends(require_admin),
):
    if not _SB:
        raise HTTPException(status_code=503, detail="Database not configured.")
    try:
        rows = _query_view("v_users_overview", order_col="registered_at", desc=True, limit=limit)
        if not rows:
            rows = _users_fallback(limit)
        # Normalise keys for frontend
        users = []
        for r in rows:
            users.append({
                "email": r.get("email"),
                "name": r.get("name"),
                "registered_at": r.get("registered_at"),
                "last_sign_in_at": r.get("last_sign_in_at"),
                "subscription_tier": r.get("subscription_tier"),
                "has_chart": r.get("chart_saved_at") is not None if r.get("has_chart") is None else bool(r.get("has_chart")),
                "has_full_chart": r.get("has_full_chart"),
                "sun_sign": r.get("sun_sign"),
                "moon_sign": r.get("moon_sign"),
                "ascendant": r.get("ascendant"),
                "birth_place": r.get("birth_place"),
                "current_city": r.get("current_city"),
                "current_timezone": r.get("current_timezone"),
                "chart_saved_at": r.get("chart_saved_at"),
            })
        return {"users": users, "count": len(users)}
    except Exception as exc:
        logger.exception("admin users failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not load users.")


@router.get("/locations")
@limiter.limit("30/minute")
def admin_locations(
    request: Request,
    _admin: AuthUser = Depends(require_admin),
):
    if not _SB:
        raise HTTPException(status_code=503, detail="Database not configured.")
    try:
        birth = _query_view("v_birth_places", limit=20)
        if not birth:
            sb = get_supabase()
            birth = []
            # fallback aggregate in Python if view missing
            rows = sb.table("natal_charts").select("birth_form").execute().data or []
            counts: dict[str, int] = {}
            for row in rows:
                bf = row.get("birth_form") or {}
                place = (bf.get("place_of_birth") or "Unknown").strip() or "Unknown"
                counts[place] = counts.get(place, 0) + 1
            birth = [{"birth_place": k, "users": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])][:20]

        cities = _query_view("v_user_cities", limit=20)
        if not cities:
            sb = get_supabase()
            cities = (
                sb.table("user_locations")
                .select("city, timezone")
                .execute()
            ).data or []
            city_counts: dict[str, dict] = {}
            for row in cities:
                key = f"{row.get('city')}|{row.get('timezone')}"
                city_counts[key] = city_counts.get(key, {"city": row.get("city"), "timezone": row.get("timezone"), "users": 0})
                city_counts[key]["users"] += 1
            cities = sorted(city_counts.values(), key=lambda x: -x["users"])[:20]

        return {"birth_places": birth, "current_cities": cities}
    except Exception as exc:
        logger.exception("admin locations failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not load locations.")


@router.get("/ai-usage")
@limiter.limit("30/minute")
def admin_ai_usage(
    request: Request,
    days: int = Query(14, ge=1, le=90),
    _admin: AuthUser = Depends(require_admin),
):
    if not _SB:
        raise HTTPException(status_code=503, detail="Database not configured.")
    since = (date.today() - timedelta(days=days - 1)).isoformat()
    try:
        rows = _query_view("v_ai_usage_daily", order_col="usage_date", desc=True, limit=days)
        if rows:
            rows = [r for r in rows if r.get("usage_date") >= since]
            rows.reverse()
        else:
            sb = get_supabase()
            raw = (
                sb.table("ai_usage")
                .select("usage_date, chat_count, forecast_count, user_id")
                .gte("usage_date", since)
                .order("usage_date")
                .execute()
            ).data or []
            by_date: dict[str, dict] = {}
            for r in raw:
                d = r["usage_date"]
                if d not in by_date:
                    by_date[d] = {"usage_date": d, "total_chat_calls": 0, "total_forecast_calls": 0, "users": set()}
                by_date[d]["total_chat_calls"] += r.get("chat_count") or 0
                by_date[d]["total_forecast_calls"] += r.get("forecast_count") or 0
                by_date[d]["users"].add(r.get("user_id"))
            rows = []
            for d in sorted(by_date.keys()):
                entry = by_date[d]
                rows.append({
                    "usage_date": entry["usage_date"],
                    "total_chat_calls": entry["total_chat_calls"],
                    "total_forecast_calls": entry["total_forecast_calls"],
                    "active_ai_users": len(entry["users"]),
                })
        return {"days": rows}
    except Exception as exc:
        logger.exception("admin ai-usage failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not load AI usage.")


@router.get("/signups")
@limiter.limit("30/minute")
def admin_signups(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    _admin: AuthUser = Depends(require_admin),
):
    if not _SB:
        raise HTTPException(status_code=503, detail="Database not configured.")
    since = (date.today() - timedelta(days=days - 1)).isoformat()
    try:
        rows = _query_view("v_signups_daily", order_col="signup_date", desc=True, limit=days)
        if rows:
            rows = [r for r in rows if r.get("signup_date") >= since]
            rows.reverse()
        else:
            sb = get_supabase()
            users = (
                sb.table("users")
                .select("created_at")
                .gte("created_at", since)
                .execute()
            ).data or []
            counts: dict[str, int] = {}
            for u in users:
                d = (u.get("created_at") or "")[:10]
                if d:
                    counts[d] = counts.get(d, 0) + 1
            rows = [{"signup_date": k, "new_users": counts[k]} for k in sorted(counts.keys())]
        return {"signups": rows}
    except Exception as exc:
        logger.exception("admin signups failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not load signups.")
