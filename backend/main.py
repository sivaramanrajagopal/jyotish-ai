"""
main.py — Jyotish AI FastAPI backend
=====================================
Phase 1: Panchangam + Natal Chart endpoints.

Security hardening (OWASP Top 10):
  A01 Broken Access Control  — bulk-preload requires secret header
  A02 Cryptographic Failures — secrets only via env vars, never in code
  A03 Injection              — Supabase SDK (parameterised), Pydantic validation
  A05 Security Misconfiguration — CORS locked to env-defined origins
  A06 Vulnerable Components  — pinned versions in requirements.txt
  A07 Auth Failures          — JWT verification on user_id routes (Step 3)
  A08 Data Integrity         — input length caps on all free-text fields
  A09 Logging                — tracebacks never sent to client
"""

import os
import re
from contextlib import asynccontextmanager
import datetime as _dt_module
from datetime import date, datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")  # explicit path — works from any cwd
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from rate_limit import limiter, client_ip
from auth import AuthUser, get_current_user, get_current_user_optional, resolve_user_id
from chart_store import load_natal_chart, resolve_natal_chart, save_natal_chart
from chart_utils import round_score, assert_chart_not_stale
from ai_limits import check_ai_quota, moderate_messages
from analytics import track_event
from security import (
    IS_PRODUCTION,
    check_content_length,
    cors_origin_for_request,
    validate_client_natal_chart,
    verify_admin_token,
)

from agents.panchangam_agent import (
    LOCATIONS,
    calculate_panchangam,
    format_validation_output,
)
from agents.natal_agent import calculate_natal_chart, format_chart_output
from agents.orchestrator import assemble_context
from agents.narrator import generate_forecast
from agents.chat_agent import chat as jyotish_chat
from agents.ashtama_agent import router as ashtama_router
from agents.transit_score_agent import score_all_houses, build_house_context
from agents.ashtakavarga_agent import calculate_ashtakavarga, bav_context_for_narrator
from agents.sky_today_agent import build_sky_today
from agents.prashna import analyze_prashna
from admin_router import router as admin_router
from geopy.geocoders import Photon
from pydantic import BaseModel

# ── Optional Supabase caching (skip gracefully if not configured) ──
try:
    from supabase_client import get_supabase
    SUPABASE_ENABLED = True
except Exception:
    SUPABASE_ENABLED = False

# ─────────────────────────────────────────────
# Scheduler lifespan
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start APScheduler on startup; shut it down cleanly on exit."""
    from production_check import run_production_checks
    run_production_checks()

    from agents.ashtama_agent import daily_personal_panchangam_job

    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    # Run daily at 04:30 IST — after midnight moon-sign changes have settled
    scheduler.add_job(
        daily_personal_panchangam_job,
        CronTrigger(hour=4, minute=30, timezone="Asia/Kolkata"),
        id="daily_personal_panchangam",
        replace_existing=True,
    )
    scheduler.start()
    print("[scheduler] APScheduler started — daily_personal_panchangam @ 04:30 IST")

    yield  # app runs here

    scheduler.shutdown(wait=False)
    print("[scheduler] APScheduler stopped")


# ─────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────

# ── Rate limiter (see rate_limit.py — X-Forwarded-For aware) ─────────────────

# ── CORS: read allowed origins from env (NEVER use * in production) ───────────
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
ALLOWED_ORIGINS_LIST = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app = FastAPI(
    title="Parashara Jyotish API",
    description="Vedic astrology — Natal chart, Dasha, Gochara, Panchangam, Ashtakavarga",
    version="0.1.0",
    lifespan=lifespan,
    # Disable auto-generated docs in production to reduce attack surface
    docs_url="/docs" if os.getenv("APP_ENV") != "production" else None,
    redoc_url="/redoc" if os.getenv("APP_ENV") != "production" else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors without request body (PII)."""
    import logging
    logging.getLogger(__name__).error(
        "422 validation error on %s %s: %s",
        request.method, request.url.path, exc.errors(),
    )
    msgs = [f"{' → '.join(str(l) for l in e['loc'])}: {e['msg']}" for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": " | ".join(msgs)})

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS_LIST,
    allow_credentials=False,   # no cookies/sessions yet — keep False
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type", "Authorization", "X-Admin-Token"],
)

@app.middleware("http")
async def limit_request_body_size(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        check_content_length(request)
    return await call_next(request)

# ── Security headers middleware ────────────────────────────────────────────────
# NOTE: @app.middleware("http") wraps outermost — runs before CORS.
# We must never raise here or CORS headers will be missing on error responses.
@app.middleware("http")
async def security_headers(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Unhandled error in request pipeline")
        cors_headers = {}
        origin = cors_origin_for_request(request, ALLOWED_ORIGINS_LIST)
        if origin:
            cors_headers["Access-Control-Allow-Origin"] = origin
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers=cors_headers,
        )
    response.headers["X-Content-Type-Options"]  = "nosniff"
    response.headers["X-Frame-Options"]         = "DENY"
    response.headers["X-XSS-Protection"]        = "1; mode=block"
    response.headers["Referrer-Policy"]         = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]      = "geolocation=(), microphone=(), camera=()"
    if IS_PRODUCTION:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.include_router(ashtama_router)
app.include_router(admin_router)

# ─────────────────────────────────────────────
# Auth (Step 3)
# ─────────────────────────────────────────────

@app.get("/auth/me")
@limiter.limit("60/minute")
def auth_me(request: Request, user: AuthUser = Depends(get_current_user)):
    """Return the authenticated user from a valid Supabase JWT."""
    from admin_auth import is_admin_email

    return {
        "user_id": user.id,
        "email": user.email,
        "is_admin": is_admin_email(user.email),
    }


@app.get("/auth/usage")
@limiter.limit("60/minute")
def auth_usage(request: Request, user: AuthUser = Depends(get_current_user)):
    """Today's AI quota usage for signed-in users."""
    from ai_limits import get_ai_usage

    return get_ai_usage(user.id)


@app.get("/auth/anon-usage")
@limiter.limit("60/minute")
def auth_anon_usage(request: Request):
    """Today's AI quota for guest users (hashed IP, no PII returned)."""
    from ai_limits import get_anon_ai_usage

    return get_anon_ai_usage(client_ip(request))


@app.delete("/auth/account")
@limiter.limit("5/hour")
def auth_delete_account(request: Request, user: AuthUser = Depends(get_current_user)):
    """Permanently delete account, chart, and AI usage data."""
    from account_delete import delete_user_account

    delete_user_account(user.id)
    track_event("account_deleted", user_id=user.id)
    return {"deleted": True}


# ── Input sanitiser (strip control chars + HTML tags from free-text) ──────────
_HTML_TAG_RE = re.compile(r"<[^>]+>")

def _sanitise(text: str, max_len: int = 200) -> str:
    """Strip HTML tags and control characters; enforce max length."""
    if not text:
        return ""
    text = _HTML_TAG_RE.sub("", text)
    # Remove non-printable control chars except newline/tab
    text = "".join(c for c in text if c.isprintable() or c in "\n\t")
    return text[:max_len].strip()


# ─────────────────────────────────────────────
# Helper: fetch from cache or calculate
# ─────────────────────────────────────────────

def _get_panchangam(date_str: str, location: str) -> dict:
    """Check Supabase cache first; compute and store on miss."""
    if location not in LOCATIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown location '{location}'. "
                   f"Valid options: {list(LOCATIONS.keys())}",
        )

    # ── Cache lookup ──────────────────────────────────────────
    if SUPABASE_ENABLED:
        try:
            sb = get_supabase()
            cached = (
                sb.table("panchangam_daily")
                .select("*")
                .eq("date", date_str)
                .eq("location_name", location)
                .maybe_single()
                .execute()
            )
            if cached and cached.data:
                return cached.data
        except Exception as e:
            print(f"[supabase cache miss] {e}")

    # ── Compute ───────────────────────────────────────────────
    result = calculate_panchangam(date_str, location)

    # ── Store in Supabase (strip computed-only fields not in DB schema) ──
    DB_EXCLUDE = {"ayanamsa", "ayanamsa_value"}
    db_row = {k: v for k, v in result.items() if k not in DB_EXCLUDE}

    if SUPABASE_ENABLED:
        try:
            sb = get_supabase()
            sb.table("panchangam_daily").upsert(db_row).execute()
        except Exception as e:
            print(f"[supabase write error] {e}")

    return result


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/")
@limiter.limit("60/minute")
def root(request: Request):
    return {"status": "ok", "service": "Parashara Jyotish", "version": "0.1.0"}


@app.get("/ping")
@limiter.limit("120/minute")
def ping(request: Request):
    """
    Lightweight keep-alive endpoint for Render free tier.
    Frontend polls this every 10 minutes to prevent the 50s cold-start.
    """
    return {"pong": True}


@app.get("/health")
@limiter.limit("60/minute")
def health(request: Request):
    """Dependency check for uptime monitors."""
    checks = {"api": "ok", "supabase": "skipped", "ephemeris": "ok"}
    if SUPABASE_ENABLED:
        try:
            sb = get_supabase()
            sb.table("users").select("id").limit(1).execute()
            checks["supabase"] = "ok"
        except Exception:
            checks["supabase"] = "error"
    try:
        import swisseph as swe
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        checks["ephemeris"] = "ok"
    except Exception:
        checks["ephemeris"] = "error"
    status = "ok" if all(v == "ok" or v == "skipped" for v in checks.values()) else "degraded"
    code = 200 if status == "ok" else 503
    return JSONResponse(status_code=code, content={"status": status, "checks": checks})


@app.get("/panchangam/locations")
@limiter.limit("60/minute")
def list_locations(request: Request):
    """List all supported locations."""
    return {
        "locations": [
            {
                "name": name,
                "lat": info["lat"],
                "lon": info["lon"],
                "timezone": info["tz"],
            }
            for name, info in LOCATIONS.items()
        ]
    }


@app.get("/panchangam/today")
@limiter.limit("60/minute")
def panchangam_today(request: Request, location: str = Query("Chennai", description="Location name")):
    """
    Get today's Panchangam for a location.
    Checks Supabase cache first; calculates and stores on miss.
    """
    today = date.today().isoformat()
    return _get_panchangam(today, location)


@app.get("/sky/today")
@limiter.limit("120/minute")
def sky_today(
    request: Request,
    location: str = Query("Chennai", description="Location for panchangam & kalam"),
    moon_nak_index: Optional[int] = Query(None, ge=0, le=26, description="Natal Moon nakshatra index"),
    moon_rasi_index: Optional[int] = Query(None, ge=0, le=11, description="Natal Moon rasi index"),
    natal_asc_sign_index: Optional[int] = Query(None, ge=0, le=11, description="Natal ascendant sign index"),
):
    """
    Compact cosmos strip: today's sky + optional personal Tara / Moon house / alerts.
    """
    if location not in LOCATIONS:
        # Allow fuzzy place strings (e.g. "Chennai, India")
        from agents.sky_today_agent import _resolve_location
        location = _resolve_location(location)

    try:
        return build_sky_today(
            location=location,
            moon_nak_index=moon_nak_index,
            moon_rasi_index=moon_rasi_index,
            natal_asc_sign_index=natal_asc_sign_index,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("sky/today error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Sky data unavailable. Please try again.")


@app.get("/panchangam/date")
@limiter.limit("60/minute")
def panchangam_by_date(
    request: Request,
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    location: str = Query("Chennai", description="Location name"),
):
    """
    Get Panchangam for a specific date and location.
    Always caches result in Supabase.
    """
    # Validate date format — strict regex first, then datetime parse
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date value.")
    return _get_panchangam(date, location)


@app.post("/panchangam/bulk-preload")
@limiter.limit("5/hour")
def bulk_preload(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to preload"),
    location: str = Query("Chennai", description="Location name"),
    _: None = Depends(verify_admin_token),
):
    """
    Pre-calculate and store Panchangam for the next N days for a location.
    Admin only — requires X-Admin-Token header (never query string).
    """
    if location not in LOCATIONS:
        raise HTTPException(status_code=400, detail=f"Unknown location '{location}'.")

    results = []
    start = date.today()
    errors = []

    for i in range(days):
        d = (start + __import__("datetime").timedelta(days=i)).isoformat()
        try:
            _get_panchangam(d, location)
            results.append({"date": d, "status": "ok"})
        except Exception:
            errors.append({"date": d, "status": "error"})

    return {
        "location": location,
        "requested_days": days,
        "success": len(results),
        "errors": len(errors),
    }


@app.get("/panchangam/validate-today", response_class=PlainTextResponse)
@limiter.limit("10/minute")
def validate_today(
    request: Request,
    location: str = Query("Chennai", description="Location name"),
    force: bool = Query(False, description="Bypass Supabase cache and recalculate fresh"),
):
    """
    Debug endpoint — disabled in production. Compare Panchangam against reference.
    """
    if IS_PRODUCTION:
        raise HTTPException(status_code=404, detail="Not found.")
    today = date.today().isoformat()
    if force:
        result = calculate_panchangam(today, location)
    else:
        result = _get_panchangam(today, location)
    output = format_validation_output(result)

    # Append Prokerala reference for easy diff
    reference = """

══════════════════════════════════════════════
  PROKERALA REFERENCE (2026-05-30, Chennai)
══════════════════════════════════════════════
  Vaaram    : Shanivaram (Saturday)          ✓ expected
  Tithi     : Shukla Chaturdashi             ✓ expected
  Next Tithi: Purnima (~2:28 AM next day)    ✓ expected
  Nakshatra : Vishakha                       ✓ expected
  Rahu Kalam: 08:55 AM – 10:31 AM           ✓ expected (±5 min)

  Validation PASS if:
    - Vaaram    = Shanivaram
    - Tithi     = Chaturdashi (Shukla)
    - Nakshatra = Vishakha
    - Rahu start within 5 min of 08:55 AM
"""
    return output + reference


# ─────────────────────────────────────────────
# Natal Chart
# ─────────────────────────────────────────────

class NatalChartRequest(BaseModel):
    name: str                          # max 80 chars
    dob: str                           # YYYY-MM-DD
    tob: str                           # HH:MM (24h, local time)
    place_of_birth: str                # max 120 chars
    gender: Optional[str] = "male"
    user_id: Optional[str] = None      # if logged in

    model_config = {"str_strip_whitespace": True}

    def cleaned(self) -> dict:
        """Return sanitised dict — avoids Pydantic v2 immutability issues."""
        return {
            "name":           _sanitise(self.name, 80),
            "dob":            self.dob,
            "tob":            self.tob,
            "place_of_birth": _sanitise(self.place_of_birth, 120),
            "gender":         _sanitise(self.gender or "male", 20),
            "user_id":        self.user_id,
        }


_geocoder = Photon(user_agent="jyotish-ai/1.0", timeout=10)

# In-process cache: normalised city name → (lat, lon, tz)
_geocache: dict[str, tuple[float, float, str]] = {}


def _geocode(place: str) -> tuple[float, float, str]:
    """Return (lat, lon, timezone_str) for a place name.

    Uses Photon (Komoot/OSM) — no API key, no rate limits.
    Results are cached in-process so the same city is only looked up once.
    """
    key = place.strip().lower()

    if key in _geocache:
        return _geocache[key]

    try:
        location = _geocoder.geocode(place, language="en")
    except Exception as geo_err:
        raise HTTPException(
            status_code=503,
            detail="Geocoding service unavailable. Please try again shortly."
        )

    if not location:
        raise HTTPException(
            status_code=400,
            detail=f"Could not find '{place}'. Please use a major city name (e.g. 'Chennai', 'Mumbai')."
        )

    lat, lon = location.latitude, location.longitude

    try:
        from timezonefinder import TimezoneFinder
        tz = TimezoneFinder().timezone_at(lat=lat, lng=lon) or "UTC"
    except ImportError:
        tz = "UTC"

    result = (lat, lon, tz)
    _geocache[key] = result
    return result


@app.post("/natal-chart")
@limiter.limit("20/minute")
def natal_chart(
    request: Request,
    req: NatalChartRequest,
    auth_user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """
    Calculate a Vedic natal chart.

    - Geocodes place_of_birth to lat/lon/timezone
    - Computes full birth chart using pyswisseph + Lahiri ayanamsa
    - Stores in natal_charts table when authenticated (user_id from JWT)
    - Returns planet positions, ascendant, yogas
    """
    cleaned = req.cleaned()
    name           = cleaned["name"]
    dob            = cleaned["dob"]
    tob            = cleaned["tob"]
    place_of_birth = cleaned["place_of_birth"]
    user_id        = resolve_user_id(cleaned["user_id"], auth_user)

    # Validate date + time formats strictly
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", dob):
        raise HTTPException(status_code=400, detail="dob must be YYYY-MM-DD.")
    # Accept HH:MM or HH:MM:SS (HTML time inputs vary)
    if not re.match(r"^\d{2}:\d{2}(:\d{2})?$", tob):
        raise HTTPException(status_code=400, detail="tob must be HH:MM (24h).")
    tob = tob[:5]   # normalise to HH:MM
    try:
        datetime.strptime(dob, "%Y-%m-%d")
        datetime.strptime(tob, "%H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time format.")

    lat, lon, timezone = _geocode(place_of_birth)

    from location_utils import resolve_panchangam_location
    panchangam_location = resolve_panchangam_location(place_of_birth, lat=lat, lon=lon)

    chart = calculate_natal_chart(
        dob=dob,
        tob=tob,
        lat=lat,
        lon=lon,
        timezone=timezone,
    )

    # Add geocoded location back into response
    chart["place_of_birth"] = place_of_birth
    chart["birth_data"]["lat"] = lat
    chart["birth_data"]["lon"] = lon
    chart["birth_data"]["timezone"] = timezone
    chart["birth_data"]["place_of_birth"] = place_of_birth
    chart["birth_data"]["panchangam_location"] = panchangam_location
    chart["panchangam_location"] = panchangam_location

    # Add dasha data
    try:
        from agents.dasha_agent import get_personal_dasha
        moon_lon = chart["planet_positions"]["Moon"]["longitude"]
        chart["dasha"] = get_personal_dasha(moon_lon, dob)
    except Exception as e:
        print(f"[dasha error] {e}")
        chart["dasha"] = {}

    # Store in Supabase if user_id provided
    if user_id and SUPABASE_ENABLED:
        birth_form = {
            "name": name,
            "dob": dob,
            "tob": tob,
            "place_of_birth": place_of_birth,
            "gender": cleaned.get("gender", "male"),
        }
        chart["birth_data"]["name"] = name
        save_natal_chart(user_id, chart, birth_form)

    track_event(
        "chart_calculated",
        user_id=user_id,
        properties={"place": place_of_birth, "panchangam_city": panchangam_location},
    )
    return chart


@app.get("/natal-chart")
@limiter.limit("60/minute")
def get_natal_chart(
    request: Request,
    auth_user: AuthUser = Depends(get_current_user),
):
    """Return the authenticated user's saved natal chart from Supabase."""
    chart = load_natal_chart(auth_user.id)
    if not chart:
        raise HTTPException(status_code=404, detail="No saved chart found.")
    return chart


# ─────────────────────────────────────────────
# Forecast
# ─────────────────────────────────────────────

class ForecastRequest(BaseModel):
    natal_chart: Optional[dict] = None
    location: str = "Chennai"  # for panchangam
    date: Optional[str] = None  # YYYY-MM-DD, defaults to today


@app.post("/forecast")
@limiter.limit("10/minute")
def forecast(
    request: Request,
    req: ForecastRequest,
    auth_user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """
    Generate a personalized daily Vedic forecast using Claude AI.

    Combines natal chart + Vimshottari Dasha + today's Panchangam,
    then sends to Claude for narrated sections.

    Requires ANTHROPIC_API_KEY in backend/.env.
    Get a key at: https://console.anthropic.com
    """
    check_ai_quota(auth_user.id if auth_user else None, "forecast", client_ip(request))
    chart = resolve_natal_chart(req.natal_chart, auth_user.id if auth_user else None, _sanitise)
    assert_chart_not_stale(chart)
    try:
        context = assemble_context(
            natal_chart=chart,
            location=req.location,
            target_date=req.date,
        )
        result = generate_forecast(context)
        return {
            "date":          context["date"],
            "location":      context["location"],
            "career":        result.get("career", ""),
            "love":          result.get("love", ""),
            "health":        result.get("health", ""),
            "spiritual":     result.get("spiritual", ""),
            "finance":       result.get("finance", ""),
            "timing_advice": result.get("timing_advice", ""),
            "dasha_context": result.get("dasha_context", ""),
            "model":         result.get("model", ""),
        }
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Forecast service temporarily unavailable.")
    except Exception:
        raise HTTPException(status_code=500, detail="Forecast service temporarily unavailable.")


# ─────────────────────────────────────────────
# Chat
# ─────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str       # "user" or "assistant"
    content: str    # will be truncated to 2000 chars

class ChatRequest(BaseModel):
    natal_chart: Optional[dict] = None
    messages: list[ChatMessage]
    location: str = "Chennai"
    language: str = "english"     # "english" | "tamil"

    model_config = {"str_strip_whitespace": True}


# ─────────────────────────────────────────────
# Transit Chart (sky positions for any date)
# ─────────────────────────────────────────────

@app.get("/transit-chart")
@limiter.limit("60/minute")
def transit_chart(
    request: Request,
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    location: str = Query("Chennai", description="Location name for timezone & ascendant"),
):
    """
    Compute planetary transit positions for a given date and location.
    Uses noon (12:00) local time. Returns planet positions + ascendant
    in the same format as /natal-chart, ready to feed SouthIndianChart.
    """
    # Validate date — strict regex + parse
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date value.")

    if location not in LOCATIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown location '{location}'. Valid: {list(LOCATIONS.keys())}",
        )

    try:
        from agents.natal_agent import (
            _to_jd, _lon_to_sign, _lon_to_nakshatra, _navamsa_sign_idx,
            _house_number, _planet_retrograde,
            PLANETS, SIGNS, SIGN_LORDS,
        )
        import ephemeris as swe
        from zoneinfo import ZoneInfo

        loc        = LOCATIONS[location]
        tz         = ZoneInfo(loc["tz"])
        lat        = loc["lat"]
        lon_coord  = loc["lon"]

        # Noon on the given date in the location's timezone
        year, month, day = [int(x) for x in date.split("-")]
        dt_noon = datetime(year, month, day, 12, 0, 0, tzinfo=tz)
        jd = _to_jd(dt_noon)

        # Ayanamsa (Lahiri — enforced in ephemeris wrapper)
        ayanamsa_val = swe.get_ayanamsa_ut(jd)

        # Ascendant at noon for this location
        flags = swe.FLG_SIDEREAL
        cusps, ascmc = swe.houses_ex(jd, lat, lon_coord, b"W", flags)
        asc_lon_sid  = ascmc[0] % 360
        asc_sign, asc_deg = _lon_to_sign(asc_lon_sid)
        asc_sign_idx = SIGNS.index(asc_sign)
        asc_nak, asc_nak_lord, asc_pada = _lon_to_nakshatra(asc_lon_sid)

        # Planets
        planet_positions = {}
        for name, pid in PLANETS.items():
            xx, _ = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            sid_lon = xx[0] % 360
            sign, deg_in_sign = _lon_to_sign(sid_lon)
            nak, nak_lord, pada = _lon_to_nakshatra(sid_lon)
            sign_idx = SIGNS.index(sign)
            retro    = _planet_retrograde(name, pid, jd, xx[3])
            nav_idx  = _navamsa_sign_idx(sid_lon)
            vargo    = (nav_idx == sign_idx)
            planet_positions[name] = {
                "longitude":     sid_lon,
                "sign":          sign,
                "sign_index":    sign_idx,
                "sign_lord":     SIGN_LORDS[sign],
                "house":         _house_number(sign_idx, asc_sign_idx),
                "nakshatra":     nak,
                "nakshatra_lord":nak_lord,
                "pada":          pada,
                "degree_in_sign":deg_in_sign,
                "retrograde":    retro,
                "vargottama":    vargo,
            }

        # Add Ketu (always 180° from Rahu)
        rahu_lon = planet_positions["Rahu"]["longitude"]
        ketu_lon  = (rahu_lon + 180) % 360
        k_sign, k_deg = _lon_to_sign(ketu_lon)
        k_nak, k_nak_lord, k_pada = _lon_to_nakshatra(ketu_lon)
        k_sign_idx = SIGNS.index(k_sign)
        planet_positions["Ketu"] = {
            "longitude":     ketu_lon,
            "sign":          k_sign,
            "sign_index":    k_sign_idx,
            "sign_lord":     SIGN_LORDS[k_sign],
            "house":         _house_number(k_sign_idx, asc_sign_idx),
            "nakshatra":     k_nak,
            "nakshatra_lord":k_nak_lord,
            "pada":          k_pada,
            "degree_in_sign":k_deg,
            "retrograde":    True,  # Ketu always retrograde (Vedic)
            "vargottama":    _navamsa_sign_idx(ketu_lon) == k_sign_idx,
        }

        return {
            "date":     date,
            "location": location,
            "time":     "12:00 (noon local)",
            "ayanamsa": "Lahiri",
            "ayanamsa_value": ayanamsa_val,
            "ascendant": {
                "sign":          asc_sign,
                "sign_index":    asc_sign_idx,
                "sign_lord":     SIGN_LORDS[asc_sign],
                "degree_in_sign":asc_deg,
                "nakshatra":     asc_nak,
                "nakshatra_lord":asc_nak_lord,
                "pada":          asc_pada,
            },
            "planet_positions": planet_positions,
        }

    except Exception as e:
        import traceback, logging
        logging.getLogger(__name__).error("Transit chart error: %s\n%s", e, traceback.format_exc())
        # Never leak internal tracebacks to the client
        raise HTTPException(status_code=500, detail="Transit chart computation failed. Please try again.")


@app.post("/chat")
@limiter.limit("30/minute")
def chat_endpoint(
    request: Request,
    req: ChatRequest,
    auth_user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """
    Multi-turn Vedic astrology chat grounded in the user's natal chart.
    Pass the full conversation history with each request.
    Requires OPENAI_API_KEY in backend/.env.
    """
    check_ai_quota(auth_user.id if auth_user else None, "chat", client_ip(request))
    # Enforce message count and content length caps (cost control + DoS prevention)
    MAX_MESSAGES = 40
    MAX_MSG_LEN  = 2000

    if len(req.messages) > MAX_MESSAGES:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_MESSAGES} messages per request.")

    # Sanitise each message — strip HTML tags, cap length
    msgs = []
    for m in req.messages:
        role = m.role if m.role in ("user", "assistant") else "user"
        content = _sanitise(m.content, MAX_MSG_LEN)
        if content:
            msgs.append({"role": role, "content": content})

    if not msgs:
        raise HTTPException(status_code=400, detail="No valid messages provided.")

    moderate_messages(msgs)
    chart = resolve_natal_chart(req.natal_chart, auth_user.id if auth_user else None, _sanitise)
    assert_chart_not_stale(chart)

    try:
        reply = jyotish_chat(natal_chart=chart, messages=msgs, location=req.location, language=req.language)
        track_event("chat_sent", user_id=auth_user.id if auth_user else None, properties={"language": req.language})
        return {"reply": reply, "model": "gpt-4o-mini"}
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Chat service temporarily unavailable.")
    except Exception as exc:
        import logging, traceback
        logging.getLogger(__name__).error(
            "Chat endpoint error: %s\n%s", exc, traceback.format_exc()
        )
        raise HTTPException(status_code=500, detail="Chat service temporarily unavailable.")


# ─────────────────────────────────────────────────────────────────────────────
# Deterministic Forecast — House Scores
# ─────────────────────────────────────────────────────────────────────────────

# ── Language helpers ──────────────────────────────────────────────────────────
_TAMIL_INSTRUCTION = """
=== மொழி அறிவுறுத்தல் (STRICT TAMIL ONLY) ===
உங்கள் பதில் முழுவதும் தூய தமிழில் இருக்க வேண்டும்.
தங்கிலீஷ் (Tanglish) வேண்டாம். தேவநாகரி / ஹிந்தி எழுத்துகள் வேண்டாம்.
ஆங்கில எழுத்துகளை உரை வரிகளில் கலக்காதீர்கள்.

கிரக பெயர்கள் (இவற்றை மட்டுமே பயன்படுத்தவும்):
சூரியன் | சந்திரன் | செவ்வாய் | புதன் | குரு | சுக்கிரன் | சனி | ராகு | கேது

ஜோதிட சொற்கள்:
மகாதசை = Mahadasha | புத்தி = Bhukti | பாவம் / வீடு = House
நட்சத்திரம் = Nakshatra | லக்னம் = Lagna | யோகம் = Yoga
கோசாரம் = Transit | உச்சம் = Exalted | நீசம் = Debilitated
வக்கிரம் = Retrograde | ஜன்ம ராசி = Natal Moon sign

அனுமதிக்கப்படுவன (ALLOWED in English):
H1…H12 (வீட்டு எண்கள்) | எண் மதிப்புகள் / புள்ளிகள் (scores like 71.8)
=== END INSTRUCTION ===
""".strip()


def _lang_suffix(language: str) -> str:
    """Return the Tamil instruction suffix if needed."""
    return f"\n\n{_TAMIL_INSTRUCTION}" if language.lower() == "tamil" else ""


class ForecastScoresRequest(BaseModel):
    natal_chart: Optional[dict] = None
    transit_date: Optional[str] = None

    model_config = {"str_strip_whitespace": True}


class HouseInsightRequest(BaseModel):
    natal_chart: Optional[dict] = None
    house_num:   int
    gender:      str = "unspecified"
    transit_date: Optional[str] = None
    language:    str = "english"          # "english" | "tamil"

    model_config = {"str_strip_whitespace": True}


@app.post("/forecast/scores")
@limiter.limit("30/minute")
def forecast_scores(
    request: Request,
    req: ForecastScoresRequest,
    auth_user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """
    Return deterministic RAG scores for all 12 houses.
    Cached in-process: same natal chart + same date = instant response.
    """
    chart = resolve_natal_chart(req.natal_chart, auth_user.id if auth_user else None, _sanitise)
    assert_chart_not_stale(chart)
    try:
        result = score_all_houses(chart, req.transit_date)
        return result
    except Exception as exc:
        import logging, traceback
        logging.getLogger(__name__).error(
            "forecast/scores error: %s\n%s", exc, traceback.format_exc()
        )
        raise HTTPException(status_code=500, detail="Forecast scoring failed.")


@app.post("/forecast/house")
@limiter.limit("20/minute")
def forecast_house_insight(
    request: Request,
    req: HouseInsightRequest,
    auth_user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """
    Return AI interpretation for a single house.
    Uses deterministic scores + OpenAI narrator with age/gender context.
    """
    if not 1 <= req.house_num <= 12:
        raise HTTPException(status_code=400, detail="house_num must be 1–12.")

    check_ai_quota(auth_user.id if auth_user else None, "forecast", client_ip(request))
    chart = resolve_natal_chart(req.natal_chart, auth_user.id if auth_user else None, _sanitise)
    assert_chart_not_stale(chart)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured.")

    try:
        scores = score_all_houses(chart, req.transit_date)
    except Exception as exc:
        import logging, traceback
        logging.getLogger(__name__).error("forecast/house scoring: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Forecast scoring failed.")

    # Derive age from dob
    dob_str = chart.get("birth_data", {}).get("dob", "")
    age = ""
    try:
        dob_dt = date.fromisoformat(dob_str)
        today  = date.today()
        age    = str(today.year - dob_dt.year -
                     ((today.month, today.day) < (dob_dt.month, dob_dt.day)))
    except Exception:
        pass

    house_context = build_house_context(scores, req.house_num)
    dasha_info    = chart.get("dasha", {})
    md = dasha_info.get("mahadasha", {}) if dasha_info else {}
    bh = dasha_info.get("bhukti", {})    if dasha_info else {}

    gender_note = {
        "male":   "Tailor advice for a man.",
        "female": "Tailor advice for a woman.",
    }.get(req.gender.lower(), "")

    system = (
        "You are Parashara Jyotish, a classical Vedic astrology advisor. "
        "Provide a focused, specific forecast for ONE life area based on the data below. "
        "Be direct and practical — 3 sentences max per section. "
        "Never be vague. Always name specific planets, signs, or periods. "
        f"{gender_note}"
        + _lang_suffix(req.language)
    )

    user_prompt = (
        f"Age: {age or 'unknown'}. Gender: {req.gender}.\n\n"
        f"Current Dasha: {md.get('planet','')} Mahadasha / {bh.get('planet','')} Bhukti.\n\n"
        f"{house_context}\n\n"
        "Give a forecast with three short sections:\n"
        "1. CURRENT SITUATION (what's happening now)\n"
        "2. OPPORTUNITY (what to act on)\n"
        "3. CAUTION (what to avoid or watch)"
    )

    try:
        from openai import OpenAI, APIError, AuthenticationError, RateLimitError
        client   = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=350,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_prompt},
            ],
        )
        insight = response.choices[0].message.content or ""
    except AuthenticationError:
        raise HTTPException(status_code=503, detail="OpenAI API key is invalid.")
    except RateLimitError:
        raise HTTPException(status_code=503, detail="OpenAI rate limit. Try again shortly.")
    except Exception as exc:
        import logging, traceback
        logging.getLogger(__name__).error("forecast/house AI: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail="AI service temporarily unavailable.")

    house_data = scores["houses"].get(req.house_num, {})
    return {
        "house_num":   req.house_num,
        "area":        house_data.get("area"),
        "score":       house_data.get("score"),
        "rag":         house_data.get("rag"),
        "insight":     insight,
        "lord":        house_data.get("lord"),
        "lord_house":  house_data.get("lord_placed_house"),
        "lord_dignity": house_data.get("lord_dignity"),
        "transit_planets": house_data.get("transit_planets", []),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Daily Reading — full synthesis of natal + Dasha + Gochara + Tara
# ─────────────────────────────────────────────────────────────────────────────

class DailyReadingRequest(BaseModel):
    natal_chart:  Optional[dict] = None
    gender:       str = "unspecified"
    transit_date: Optional[str] = None
    language:     str = "english"
    model_config = {"str_strip_whitespace": True}


@app.post("/forecast/daily-reading")
@limiter.limit("15/minute")
def forecast_daily_reading(
    request: Request,
    req: DailyReadingRequest,
    auth_user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """
    Synthesise natal chart + Dasha + Gochara + Tara Balam into a
    3-5 sentence daily reading with a Dasha-Transit correlation score.
    """
    check_ai_quota(auth_user.id if auth_user else None, "forecast", client_ip(request))
    chart = resolve_natal_chart(req.natal_chart, auth_user.id if auth_user else None, _sanitise)
    assert_chart_not_stale(chart)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured.")

    # ── Scores + Dasha-Transit correlation ────────────────────────────────
    try:
        from agents.transit_score_agent import (
            score_all_houses, dasha_transit_correlation, compact_gochara_summary
        )
        scores = score_all_houses(chart, req.transit_date)
        dasha  = chart.get("dasha", {}) or {}
        dtc    = dasha_transit_correlation(scores, dasha)
    except Exception as exc:
        import logging, traceback
        logging.getLogger(__name__).error("daily-reading scoring: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Forecast scoring failed.")

    # ── Derive age ─────────────────────────────────────────────────────────
    dob_str = chart.get("birth_data", {}).get("dob", "")
    age = ""
    try:
        dob_d = date.fromisoformat(dob_str)
        today = date.today()
        age   = str(today.year - dob_d.year - ((today.month, today.day) < (dob_d.month, dob_d.day)))
    except Exception:
        pass

    md = (dasha.get("mahadasha") or {})
    bh = (dasha.get("bhukti")    or {})

    oh = scores["overall_health"]
    top3 = sorted(scores["houses"].values(), key=lambda x: x["score"], reverse=True)[:3]
    bot3 = sorted(scores["houses"].values(), key=lambda x: x["score"])[:3]

    # ── Tara Balam context (respects transit_date when provided) ───────────
    tara_context = ""
    try:
        from agents.tara_engine import compute_all as _tara_all
        from zoneinfo import ZoneInfo
        bd       = chart.get("birth_data", {})
        nak_idx  = chart.get("moon_nakshatra_index")
        rasi_idx = chart.get("moon_rasi_index")
        if nak_idx is not None and rasi_idx is not None:
            tz_id = bd.get("timezone", "Asia/Kolkata")
            td    = date.fromisoformat(req.transit_date) if req.transit_date else date.today()
            dt    = datetime(td.year, td.month, td.day, 12, 0, 0, tzinfo=ZoneInfo(tz_id))
            pp    = _tara_all(int(nak_idx), int(rasi_idx), dt, tz_id)
            tara  = pp.get("tara", {})
            day_lbl = "today" if td == date.today() else td.isoformat()
            tara_context = (
                f"Tara Balam ({day_lbl}): {tara.get('name')} (Tara {tara.get('position')}) — "
                f"{tara.get('nature')}. {tara.get('meaning', '')}"
            )
    except Exception:
        pass

    # ── Ashtakavarga (SAV) context ─────────────────────────────────────────
    sav_context = ""
    try:
        sav_context = bav_context_for_narrator(chart)
    except Exception:
        pass

    system = (
        "You are Parashara Jyotish, a classical Vedic astrology advisor. "
        "Write a concise daily reading (4–5 sentences) synthesising ALL available data: "
        "natal chart strength, current Dasha period, Gochara transit health, "
        "Ashtakavarga (SAV) house bindus, and Tara Balam. "
        "Be specific — name planets, houses, SAV scores, and periods. No disclaimers. No generic statements. "
        f"{'Tailor the language for a man.' if req.gender.lower()=='male' else 'Tailor the language for a woman.' if req.gender.lower()=='female' else ''}"
        + _lang_suffix(req.language)
    )

    user_prompt = (
        f"Age: {age or 'unknown'}. Gender: {req.gender}.\n"
        f"Current Dasha: {md.get('planet','')} Mahadasha ({md.get('remaining_years','')} yrs left) / "
        f"{bh.get('planet','')} Bhukti ({bh.get('remaining_months','')} months left).\n"
        f"Dasha-Transit correlation: {dtc['rag']['label']} ({round_score(dtc['correlation_score'])}/100). {dtc['overall']}\n"
        f"{dtc['summary']}\n\n"
        f"Overall transit health: {round_score(oh['average_score'])}/100 [{oh['rag']['label']}]\n"
        f"Strongest areas today: {', '.join(h['name'] for h in top3)}\n"
        f"Most challenging areas: {', '.join(h['name'] for h in bot3)}\n"
        f"{tara_context}\n\n"
        + (f"{sav_context}\n\n" if sav_context else "")
        + "Write the daily reading as a single flowing paragraph. "
        "Start with the Dasha-Transit correlation, then the strongest/weakest areas, "
        "mention any notable SAV-strong or SAV-weak houses, then practical guidance for today."
    )

    try:
        from openai import OpenAI, AuthenticationError, RateLimitError
        client   = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=300,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_prompt},
            ],
        )
        reading = response.choices[0].message.content or ""
    except AuthenticationError:
        raise HTTPException(status_code=503, detail="OpenAI API key is invalid.")
    except RateLimitError:
        raise HTTPException(status_code=503, detail="OpenAI rate limit. Try again shortly.")
    except Exception as exc:
        import logging, traceback
        logging.getLogger(__name__).error("forecast/house AI: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail="AI service temporarily unavailable.")

    return {
        "reading":              reading,
        "dasha_transit":        dtc,
        "overall_health":       oh,
        "top_houses":           [{"house": h["house_num"], "name": h["name"],
                                  "score": h["score"], "rag": h["rag"]} for h in top3],
        "challenging_houses":   [{"house": h["house_num"], "name": h["name"],
                                  "score": h["score"], "rag": h["rag"]} for h in bot3],
        "transit_date":         scores["transit_date"],
        "natal_moon":           scores.get("natal_moon_en", ""),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Ashtakavarga
# ─────────────────────────────────────────────────────────────────────────────

class AshtakavargaRequest(BaseModel):
    natal_chart: Optional[dict] = None
    model_config = {"str_strip_whitespace": True}


@app.post("/ashtakavarga")
@limiter.limit("30/minute")
def ashtakavarga_endpoint(
    request: Request,
    req: AshtakavargaRequest,
    auth_user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """
    Calculate Bhinnashtakavarga (BAV) + Sarvashtakavarga (SAV)
    including Trikona Shodhana, Ekadhipatya Shodhana, and Shodhya Pinda.
    Results are cached — same chart always returns instantly.
    """
    chart = resolve_natal_chart(req.natal_chart, auth_user.id if auth_user else None, _sanitise)
    assert_chart_not_stale(chart)
    try:
        result = calculate_ashtakavarga(chart)
        if not result:
            raise HTTPException(status_code=422, detail="Could not extract planet positions from natal chart.")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        import logging, traceback
        logging.getLogger(__name__).error(
            "Ashtakavarga error: %s\n%s", exc, traceback.format_exc()
        )
        raise HTTPException(status_code=500, detail="Ashtakavarga calculation failed.")


# ─────────────────────────────────────────────────────────────────────────────
# Prashna (Horary)
# ─────────────────────────────────────────────────────────────────────────────

PRASHNA_CATEGORIES = frozenset({
    "career", "marriage", "money", "property", "health", "travel", "education", "general",
    "lost_and_found", "competitive_exam", "key_interest",
})


class PrashnaAnalyzeRequest(BaseModel):
    category: str
    timestamp: str
    question_id: Optional[str] = None
    question: Optional[str] = None
    timezone: str = "Asia/Kolkata"
    lat: Optional[float] = None
    lon: Optional[float] = None
    place: Optional[str] = None
    include_ai: bool = True
    language: str = "english"
    model_config = {"str_strip_whitespace": True}


@app.post("/prashna/analyze")
@limiter.limit("20/minute")
def prashna_analyze(
    request: Request,
    req: PrashnaAnalyzeRequest,
    auth_user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """
    Cast a Prashna chart at question time and return rule-based testimonies + verdict.
    Optional AI narration (Phase 2) uses only pre-computed testimonies.
    """
    cat = (req.category or "").lower().strip()
    if cat not in PRASHNA_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid category. Choose one of: {', '.join(sorted(PRASHNA_CATEGORIES))}",
        )

    from agents.prashna.constants import resolve_question
    try:
        qid, qtext = resolve_question(cat, req.question_id, req.question)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if len(qtext) > 500:
        raise HTTPException(status_code=422, detail="Question must be at most 500 characters.")

    try:
        result = analyze_prashna(
            question=qtext,
            category=cat,
            timestamp_iso=req.timestamp,
            timezone=req.timezone or "Asia/Kolkata",
            lat=req.lat,
            lon=req.lon,
            place=req.place,
            question_id=qid,
        )

        if req.include_ai:
            check_ai_quota(auth_user.id if auth_user else None, "forecast", client_ip(request))
            from agents.prashna.ai_narrator import narrate_prashna
            ai_reading = narrate_prashna(result, req.language or "english")
            if ai_reading:
                result["ai_reading"] = ai_reading
                result["interpretation"]["ai_note"] = (
                    "AI narration below is based solely on the computed testimonies above."
                )

        track_event("prashna_analyze", properties={"category": cat, "question_id": qid})
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        import logging, traceback
        logging.getLogger(__name__).error("prashna/analyze: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Prashna analysis failed.")


@app.get("/prashna/categories")
def prashna_categories():
    from agents.prashna.constants import (
        CATEGORY_LABELS, CATEGORY_HOUSE, CATEGORY_ICONS, CATEGORY_QUESTIONS,
    )
    return {
        "categories": [
            {
                "key": k,
                "label": CATEGORY_LABELS[k],
                "house": CATEGORY_HOUSE[k],
                "icon": CATEGORY_ICONS.get(k, "🔮"),
                "questions": CATEGORY_QUESTIONS.get(k, []),
            }
            for k in sorted(CATEGORY_LABELS.keys())
        ]
    }
