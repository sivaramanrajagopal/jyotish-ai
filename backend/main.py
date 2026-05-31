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
  A07 Auth Failures          — rate limiting on AI + geocoding endpoints
  A08 Data Integrity         — input length caps on all free-text fields
  A09 Logging                — tracebacks never sent to client
"""

import os
import re
from contextlib import asynccontextmanager
from datetime import date, datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")  # explicit path — works from any cwd
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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
from geopy.geocoders import Nominatim
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

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/hour"])

# ── CORS: read allowed origins from env (NEVER use * in production) ───────────
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
ALLOWED_ORIGINS_LIST = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app = FastAPI(
    title="Jyotish AI API",
    description="Vedic astrology engine — Phase 1: Panchangam",
    version="0.1.0",
    lifespan=lifespan,
    # Disable auto-generated docs in production to reduce attack surface
    docs_url="/docs" if os.getenv("APP_ENV") != "production" else None,
    redoc_url="/redoc" if os.getenv("APP_ENV") != "production" else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors to Render logs and return a readable 422."""
    import logging
    logging.getLogger(__name__).error(
        "422 validation error on %s %s: %s | body: %s",
        request.method, request.url.path, exc.errors(), exc.body
    )
    # Return human-readable messages to the client
    msgs = [f"{' → '.join(str(l) for l in e['loc'])}: {e['msg']}" for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": " | ".join(msgs)})

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS_LIST,
    allow_credentials=False,   # no cookies/sessions yet — keep False
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# ── Security headers middleware ────────────────────────────────────────────────
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"]    = "nosniff"
    response.headers["X-Frame-Options"]           = "DENY"
    response.headers["X-XSS-Protection"]          = "1; mode=block"
    response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]        = "geolocation=(), microphone=(), camera=()"
    # CSP: allow only same-origin + our known backend (tighten after deploy)
    response.headers["Content-Security-Policy"]   = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self' https://*.supabase.co"
    )
    return response

app.include_router(ashtama_router)

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
def root():
    return {"status": "ok", "service": "Jyotish AI", "version": "0.1.0"}


@app.get("/ping")
def ping():
    """
    Lightweight keep-alive endpoint for Render free tier.
    Frontend polls this every 10 minutes to prevent the 50s cold-start.
    """
    return {"pong": True}


@app.get("/panchangam/locations")
def list_locations():
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
def bulk_preload(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to preload"),
    location: str = Query("Chennai", description="Location name"),
    x_admin_token: Optional[str] = Query(None, alias="admin_token"),
):
    """
    Pre-calculate and store Panchangam for the next N days for a location.
    Useful to run after deployment or via cron.
    """
    # Admin-only: require ADMIN_TOKEN env var
    expected_token = os.getenv("ADMIN_TOKEN", "")
    if not expected_token or x_admin_token != expected_token:
        raise HTTPException(status_code=403, detail="Forbidden.")

    if location not in LOCATIONS:
        raise HTTPException(status_code=400, detail=f"Unknown location '{location}'.")

    results = []
    start = date.today()
    errors = []

    for i in range(days):
        d = (start + __import__("datetime").timedelta(days=i)).isoformat()
        try:
            result = _get_panchangam(d, location)
            results.append({"date": d, "status": "ok"})
        except Exception as e:
            errors.append({"date": d, "error": str(e)})

    return {
        "location": location,
        "requested_days": days,
        "success": len(results),
        "errors": len(errors),
        "error_details": errors,
    }


@app.get("/panchangam/validate-today", response_class=PlainTextResponse)
def validate_today(
    location: str = Query("Chennai", description="Location name"),
    force: bool = Query(False, description="Bypass Supabase cache and recalculate fresh"),
):
    """
    Returns a formatted human-readable Panchangam output for today.
    Add ?force=true to bypass Supabase cache and force fresh calculation.
    Compare against Prokerala.com to validate.
    """
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
    user_id: Optional[str] = None      # if logged in

    # allow_mutation needed so cleaned() can write back sanitised values
    model_config = {"str_strip_whitespace": True, "arbitrary_types_allowed": True}

    def cleaned(self) -> dict:
        """Return sanitised dict — avoids Pydantic v2 immutability issues."""
        return {
            "name":           _sanitise(self.name, 80),
            "dob":            self.dob,
            "tob":            self.tob,
            "place_of_birth": _sanitise(self.place_of_birth, 120),
            "user_id":        self.user_id,
        }


_geocoder = Nominatim(user_agent="jyotish-ai")


def _geocode(place: str) -> tuple[float, float, str]:
    """Return (lat, lon, timezone_str) for a place name."""
    location = _geocoder.geocode(place, addressdetails=True, language="en")
    if not location:
        raise HTTPException(status_code=400, detail=f"Could not geocode '{place}'.")
    lat = location.latitude
    lon = location.longitude

    # Determine timezone from lat/lon using timezonefinder
    try:
        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()
        tz = tf.timezone_at(lat=lat, lng=lon) or "UTC"
    except ImportError:
        # Fallback: if country is India, use IST
        country = (location.raw.get("address") or {}).get("country_code", "").upper()
        tz = "Asia/Kolkata" if country == "IN" else "UTC"

    return lat, lon, tz


@app.post("/natal-chart")
@limiter.limit("20/minute")
def natal_chart(request: Request, req: NatalChartRequest):
    """
    Calculate a Vedic natal chart.

    - Geocodes place_of_birth to lat/lon/timezone
    - Computes full birth chart using pyswisseph + Lahiri ayanamsa
    - Stores in natal_charts table (if user_id provided)
    - Returns planet positions, ascendant, yogas
    """
    cleaned = req.cleaned()
    name           = cleaned["name"]
    dob            = cleaned["dob"]
    tob            = cleaned["tob"]
    place_of_birth = cleaned["place_of_birth"]
    user_id        = cleaned["user_id"]

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
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid date/time: {exc}")

    lat, lon, timezone = _geocode(place_of_birth)

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
        try:
            sb = get_supabase()
            asc = chart["ascendant"]
            db_row = {
                "user_id":               user_id,
                "sun_sign":              chart["planet_positions"]["Sun"]["sign"],
                "moon_sign":             chart["planet_positions"]["Moon"]["sign"],
                "ascendant":             asc["sign"],
                "planet_positions":      chart["planet_positions"],
                "yogas":                 chart["yogas"],
                "ayanamsa":              chart["ayanamsa"],
                "ayanamsa_value":        chart["ayanamsa_value"],
                "moon_nakshatra_index":  chart["moon_nakshatra_index"],
                "moon_rasi_index":       chart["moon_rasi_index"],
            }
            sb.table("natal_charts").upsert(db_row).execute()
        except Exception as e:
            print(f"[supabase natal write error] {e}")

    return chart


# ─────────────────────────────────────────────
# Forecast
# ─────────────────────────────────────────────

class ForecastRequest(BaseModel):
    natal_chart: dict           # full /natal-chart response
    location: str = "Chennai"  # for panchangam
    date: Optional[str] = None  # YYYY-MM-DD, defaults to today


@app.post("/forecast")
@limiter.limit("10/minute")
def forecast(request: Request, req: ForecastRequest):
    """
    Generate a personalized daily Vedic forecast using Claude AI.

    Combines natal chart + Vimshottari Dasha + today's Panchangam,
    then sends to Claude for narrated sections.

    Requires ANTHROPIC_API_KEY in backend/.env.
    Get a key at: https://console.anthropic.com
    """
    try:
        context = assemble_context(
            natal_chart=req.natal_chart,
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
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Forecast service temporarily unavailable.")


# ─────────────────────────────────────────────
# Chat
# ─────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str       # "user" or "assistant"
    content: str    # will be truncated to 2000 chars

class ChatRequest(BaseModel):
    natal_chart: dict
    messages: list[ChatMessage]   # full history including latest user message
    location: str = "Chennai"

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
            _house_number, _is_retrograde,
            PLANETS, SIGNS, SIGN_LORDS,
        )
        import swisseph as swe
        from zoneinfo import ZoneInfo

        loc        = LOCATIONS[location]
        tz         = ZoneInfo(loc["tz"])
        lat        = loc["lat"]
        lon_coord  = loc["lon"]

        # Noon on the given date in the location's timezone
        year, month, day = [int(x) for x in date.split("-")]
        dt_noon = datetime(year, month, day, 12, 0, 0, tzinfo=tz)
        jd = _to_jd(dt_noon)

        # Ayanamsa
        swe.set_sid_mode(swe.SIDM_LAHIRI)
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
            xx, _ = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
            sid_lon = xx[0] % 360
            sign, deg_in_sign = _lon_to_sign(sid_lon)
            nak, nak_lord, pada = _lon_to_nakshatra(sid_lon)
            sign_idx = SIGNS.index(sign)
            retro    = _is_retrograde(pid, jd)
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
            "retrograde":    False,
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
def chat_endpoint(request: Request, req: ChatRequest):
    """
    Multi-turn Vedic astrology chat grounded in the user's natal chart.
    Pass the full conversation history with each request.
    Requires OPENAI_API_KEY in backend/.env.
    """
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

    try:
        reply = jyotish_chat(natal_chart=req.natal_chart, messages=msgs, location=req.location)
        return {"reply": reply, "model": "gpt-4o-mini"}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception:
        # Never leak internal errors to client
        raise HTTPException(status_code=500, detail="Chat service temporarily unavailable.")
