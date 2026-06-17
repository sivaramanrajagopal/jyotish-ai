"""Natal Vadhai & Vainasikam — red-zone nakshatras from Janma (birth) Moon."""

from __future__ import annotations

from .constants import CONFIDENCE_MEDIUM_HIGH
from .utils import nakshatra_label


SOURCE_NOTE = (
    "Classical Tamil/Sanskrit obstruction layer: 7th and 22nd nakshatra "
    "from natal Moon are malefic transit zones (Vadhai / Vainasikam). "
    "Used in regional panchanga and obstruction-dosha traditions."
)


def compute_natal_red_zones(janma_nakshatra_index: int) -> dict:
    """
    Natal profile — NOT synastry. From birth Moon nakshatra:
      Vadhai      = 7th nakshatra  (index + 6)
      Vainasikam  = 22nd nakshatra (index + 21)
    """
    idx = int(janma_nakshatra_index) % 27
    vadhai_idx = (idx + 6) % 27
    vainasikam_idx = (idx + 21) % 27
    return {
        "janma_nakshatra": nakshatra_label(idx),
        "vadhai": {
            "ordinal": 7,
            **nakshatra_label(vadhai_idx),
            "meaning": "Danger / obstruction (Vadhai red zone)",
        },
        "vainasikam": {
            "ordinal": 22,
            **nakshatra_label(vainasikam_idx),
            "meaning": "Annihilation / severe obstruction (Vainasikam red zone)",
        },
        "confidence": CONFIDENCE_MEDIUM_HIGH,
        "source_note": SOURCE_NOTE,
    }
