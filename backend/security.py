"""
security.py — shared security helpers for the Parashara Jyotish API.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
from typing import Optional

from fastapi import Header, HTTPException, Request

logger = logging.getLogger(__name__)

MAX_JSON_BODY_BYTES = int(os.getenv("MAX_JSON_BODY_BYTES", "262144"))  # 256 KB
IS_PRODUCTION = os.getenv("APP_ENV", "development") == "production"


def cors_origin_for_request(request: Request, allowed: list[str]) -> Optional[str]:
    """Return Origin only if it is on the allowlist (never echo arbitrary origins)."""
    origin = request.headers.get("origin")
    if origin and origin in allowed:
        return origin
    return None


def verify_admin_token(x_admin_token: str = Header(..., alias="X-Admin-Token")) -> None:
    """Timing-safe admin token check — token must be sent as header, never query string."""
    expected = os.getenv("ADMIN_TOKEN", "")
    if not expected or not secrets.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=403, detail="Forbidden.")


def block_unauthenticated_user_routes() -> None:
    """
    Block user_id-scoped DB routes in production until Supabase Auth is wired.
    Frontend only uses /personal-panchangam/anonymous today.
    """
    if IS_PRODUCTION:
        raise HTTPException(
            status_code=404,
            detail="Not found.",
        )


def check_content_length(request: Request) -> None:
    """Reject oversized JSON bodies before parsing (DoS mitigation)."""
    raw = request.headers.get("content-length")
    if raw and raw.isdigit() and int(raw) > MAX_JSON_BODY_BYTES:
        raise HTTPException(status_code=413, detail="Request body too large.")


def validate_client_natal_chart(chart: dict, sanitise_fn) -> dict:
    """
    Basic integrity checks on client-supplied natal_chart before AI/scoring.
    Does not replace server-side chart storage — limits size and strips injectable text.
    """
    if not chart or not isinstance(chart, dict):
        raise HTTPException(status_code=400, detail="natal_chart is required.")
    try:
        encoded = json.dumps(chart)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid natal_chart JSON.")
    if len(encoded) > MAX_JSON_BODY_BYTES:
        raise HTTPException(status_code=413, detail="natal_chart payload too large.")
    if "birth_data" not in chart or "planet_positions" not in chart:
        raise HTTPException(status_code=400, detail="natal_chart must include birth_data and planet_positions.")

    # Sanitise free-text fields that flow into LLM prompts
    bd = chart.get("birth_data")
    if isinstance(bd, dict) and isinstance(bd.get("name"), str):
        bd["name"] = sanitise_fn(bd["name"], 80)
    if isinstance(bd, dict) and isinstance(bd.get("place_of_birth"), str):
        bd["place_of_birth"] = sanitise_fn(bd["place_of_birth"], 120)

    yogas = chart.get("yogas")
    if isinstance(yogas, list):
        for y in yogas[:20]:
            if isinstance(y, dict):
                if isinstance(y.get("name"), str):
                    y["name"] = sanitise_fn(y["name"], 80)
                if isinstance(y.get("description"), str):
                    y["description"] = sanitise_fn(y["description"], 300)

    dasha = chart.get("dasha")
    if isinstance(dasha, dict):
        for key in ("mahadasha", "bhukti"):
            block = dasha.get(key)
            if isinstance(block, dict):
                for field in ("focus", "trigger"):
                    if isinstance(block.get(field), str):
                        block[field] = sanitise_fn(block[field], 300)

    return chart


def safe_error_message(public: str, exc: Exception) -> str:
    """Log full exception server-side; return generic message to client."""
    logger.exception("%s: %s", public, exc)
    return public
