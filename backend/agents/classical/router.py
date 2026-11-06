"""POST /classical/matches — BPHS rules that apply to the chart."""

# No `from __future__ import annotations`: FastAPI must see the request model
# as a class through the rate-limit wrapper, or it reads it as a query field.
import logging
from typing import Callable, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from agents.classical import classical_enabled, classical_for_chart
from auth import AuthUser, get_current_user_optional
from chart_store import resolve_natal_chart
from chart_utils import assert_chart_not_stale
from rate_limit import limiter

logger = logging.getLogger(__name__)


class ClassicalRequest(BaseModel):
    natal_chart: Optional[dict] = None


def build_classical_router(sanitise: Callable[..., str]) -> APIRouter:
    router = APIRouter(prefix="/classical", tags=["Classical"])

    @router.post("/matches")
    @limiter.limit("30/minute")
    def classical_matches(
        request: Request,
        req: ClassicalRequest,
        auth_user: Optional[AuthUser] = Depends(get_current_user_optional),
    ):
        if not classical_enabled():
            raise HTTPException(status_code=404, detail="Not found")
        chart = resolve_natal_chart(req.natal_chart, auth_user.id if auth_user else None, sanitise)
        assert_chart_not_stale(chart)
        try:
            return classical_for_chart(chart)
        except Exception as exc:
            logger.exception("Classical rules error: %s", exc)
            raise HTTPException(status_code=500, detail="Could not match the classical rules for this chart.")

    return router
