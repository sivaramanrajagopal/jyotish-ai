"""Tamil predictive dosha — shared constants and confidence tags."""

from __future__ import annotations

CONFIDENCE_HIGH = "HIGH"
CONFIDENCE_MEDIUM = "MEDIUM"
CONFIDENCE_MEDIUM_HIGH = "MEDIUM-HIGH"
CONFIDENCE_LOW = "LOW"
CONFIDENCE_UNVERIFIED = "UNVERIFIED"

NAKSHATRA_ORDER = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

RASI_ORDER = [
    "Mesha", "Vrishabha", "Mithuna", "Kataka", "Simha", "Kanni", "Tula",
    "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena",
]

RASI_ENGLISH = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

TITHI_NAMES = {
    0: "Purnima/Amavasya",
    1: "Pratipada", 2: "Dwitiya", 3: "Tritiya", 4: "Chaturthi", 5: "Panchami",
    6: "Shashti", 7: "Saptami", 8: "Ashtami", 9: "Navami", 10: "Dashami",
    11: "Ekadashi", 12: "Dwadashi", 13: "Trayodashi", 14: "Chaturdashi",
}

# Keys 1–14; 0 = Purnima/Amavasya (no dosha)
TITHI_SOONYA_TABLE: dict[int, list[int]] = {
    1:  [6, 9],
    2:  [8, 11],
    3:  [4, 9],
    4:  [1, 10],
    5:  [2, 5],
    6:  [0, 4],   # default mesha_simha — see SHASHTI_VARIANTS
    7:  [3, 8],
    8:  [2, 5],
    9:  [4, 7],
    10: [4, 7],
    11: [8, 11],
    12: [6, 9],
    13: [1, 4],
    14: [11, 2, 5, 8],
    0:  [],
}

SHASHTI_VARIANTS = {
    "mesha_simha": [0, 4],
    "mesha_kataka": [0, 3],
}

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
] * 3

SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]

YOGA_DEG = 93 + 20 / 60
AVAYOGA_DEG = 186 + 40 / 60
