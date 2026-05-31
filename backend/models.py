"""
models.py — Pydantic request/response models for Jyotish AI API
"""

from __future__ import annotations
from datetime import date, datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Panchangam
# ─────────────────────────────────────────────

class PanchangamResponse(BaseModel):
    date: str
    location_name: str
    lat: float
    lon: float
    timezone: str
    ayanamsa: str
    ayanamsa_value: float

    sunrise: Optional[str]
    sunset: Optional[str]

    vaaram_name: str
    vaaram_lord: str

    tithi_name: str
    tithi_paksha: str
    tithi_index: int
    tithi_end_time: Optional[str]
    next_tithi_name: Optional[str]
    next_tithi_end: Optional[str]

    nakshatra_name: str
    nakshatra_lord: str
    nakshatra_index: int
    nakshatra_pada: int
    nakshatra_end_time: Optional[str]
    next_nakshatra_name: Optional[str]
    next_nakshatra_end: Optional[str]

    yogam_name: str
    yogam_index: int
    yogam_end_time: Optional[str]
    next_yogam_name: Optional[str]
    next_yogam_end: Optional[str]

    karanam_name: str
    karanam_index: int
    karanam_end_time: Optional[str]
    next_karanam_name: Optional[str]
    next_karanam_end: Optional[str]

    rahu_kalam_start: Optional[str]
    rahu_kalam_end: Optional[str]
    gulikai_kalam_start: Optional[str]
    gulikai_kalam_end: Optional[str]
    yamaganda_start: Optional[str]
    yamaganda_end: Optional[str]

    validated: bool
    calculated_at: str


# ─────────────────────────────────────────────
# Natal Chart
# ─────────────────────────────────────────────

class NatalChartRequest(BaseModel):
    name: str
    dob: str = Field(..., description="Date of birth YYYY-MM-DD")
    tob: str = Field(..., description="Time of birth HH:MM (24h, local)")
    place_of_birth: str


class PlanetPosition(BaseModel):
    lon: float
    sign: str
    house: int
    nakshatra: str
    pada: int
    retro: bool
    degree_in_sign: float


class NatalChartResponse(BaseModel):
    user_id: Optional[str]
    sun_sign: str
    moon_sign: str
    ascendant: str
    planet_positions: dict[str, Any]
    yogas: list[dict]
    ayanamsa: str
    ayanamsa_value: float
    calculated_at: str


# ─────────────────────────────────────────────
# Forecast
# ─────────────────────────────────────────────

class ForecastResponse(BaseModel):
    user_id: str
    date: str
    career_forecast: Optional[str]
    love_forecast: Optional[str]
    health_forecast: Optional[str]
    spiritual_forecast: Optional[str]
    finance_forecast: Optional[str]
    timing_advice: Optional[str]
    panchapakshi_summary: Optional[str]
    dasha_context: Optional[str]
    created_at: str


# ─────────────────────────────────────────────
# Chat
# ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    user_id: str
    message: str
    role: str = "assistant"
    created_at: str
