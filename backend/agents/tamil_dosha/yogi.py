"""Yogi / Ava Yogi / Duplicate Yogi — Hart de Fouw / Svoboda formula."""

from __future__ import annotations

from .constants import AVAYOGA_DEG, CONFIDENCE_HIGH, YOGA_DEG
from .utils import graha_at_longitude


SOURCE_NOTE = (
    "Yogi point = Sun longitude + Moon longitude + 93°20′; "
    "Avayogi point = Yogi point + 186°40′ (Hart de Fouw / Svoboda, Light on Relationships)."
)


def compute_yogi(*, sun_lon: float, moon_lon: float) -> dict:
    yogi_point = (float(sun_lon) + float(moon_lon) + YOGA_DEG) % 360
    avayogi_point = (yogi_point + AVAYOGA_DEG) % 360
    yogi_at = graha_at_longitude(yogi_point)
    ava_at = graha_at_longitude(avayogi_point)
    return {
        "yogi_point": yogi_at,
        "yogi_graha": yogi_at["nakshatra_lord"],
        "duplicate_yogi_graha": yogi_at["rasi_lord"],
        "avayogi_point": ava_at,
        "avayogi_graha": ava_at["nakshatra_lord"],
        "confidence": CONFIDENCE_HIGH,
        "source_note": SOURCE_NOTE,
    }
