"""Prashna horary constants — categories, sign modalities, planet testimonies."""

from __future__ import annotations

CATEGORY_HOUSE: dict[str, int] = {
    "career": 10,
    "marriage": 7,
    "money": 2,
    "property": 4,
    "health": 6,
    "travel": 9,
    "education": 5,
    "general": 11,
}

CATEGORY_LABELS: dict[str, str] = {
    "career": "Career / Promotion",
    "marriage": "Marriage / Relationship",
    "money": "Money / Finance",
    "property": "Property / Real Estate",
    "health": "Health",
    "travel": "Travel",
    "education": "Education",
    "general": "General",
}

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

# Movable / fixed / dual (Chara / Sthira / Dwiswa)
MOVABLE_SIGNS = {0, 3, 6, 9}
FIXED_SIGNS = {1, 4, 7, 10}
DUAL_SIGNS = {2, 5, 8, 11}

SIGN_MODALITY = {
    "movable": "Days to Weeks",
    "dual": "Weeks to Months",
    "fixed": "Months to Long Delay",
}

KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}
DUSTHANA = {6, 8, 12}

DIGNITY_STRENGTH = {
    "Exalted": "strong",
    "Own Sign": "strong",
    "Friend": "neutral",
    "Neutral": "neutral",
    "Enemy": "weak",
    "Debilitated": "weak",
    "N/A": "neutral",
}

PLANET_OCCUPANT_POSITIVE: dict[str, str] = {
    "Jupiter": "Growth, support, and opportunity indicated in this house.",
    "Venus": "Harmony and beneficial circumstances suggested.",
    "Mercury": "Communication, negotiation, and adaptability favoured.",
    "Moon": "Emotional receptivity and public support may assist the matter.",
    "Sun": "Visibility, authority, and clarity may strengthen the outcome.",
}

PLANET_OCCUPANT_CAUTION: dict[str, str] = {
    "Saturn": "Delay, responsibility, and patience required — not necessarily denial.",
    "Mars": "Competition, conflict, or urgency — energy must be channelled carefully.",
    "Rahu": "Uncertainty or unconventional paths — outcomes may be unusual.",
    "Ketu": "Detachment or separation themes — let go of rigid expectations.",
    "Sun": "Ego or authority clashes possible if poorly placed.",
    "Mercury": "Over-analysis or scattered focus may slow progress.",
}

PLANET_ASPECT_SUPPORT: dict[str, str] = {
    "Jupiter": "Jupiter's aspect suggests grace, protection, and expansion.",
    "Venus": "Venus aspect indicates cooperation and favourable conditions.",
    "Mercury": "Mercury aspect supports dialogue and practical negotiation.",
    "Moon": "Moon aspect adds emotional momentum to the matter.",
}

PLANET_ASPECT_CHALLENGE: dict[str, str] = {
    "Saturn": "Saturn aspect indicates delay, discipline, or structural obstacles.",
    "Mars": "Mars aspect shows friction, competition, or forced action.",
    "Rahu": "Rahu influence adds unpredictability or unconventional pressure.",
    "Ketu": "Ketu influence suggests detachment or incomplete fulfilment.",
    "Sun": "Solar aspect may bring authority tests or visibility pressure.",
}

PRASHNA_DISCLAIMER = (
    "This application provides automated astrological interpretations based on "
    "traditional horary astrology principles and rule-based analysis. Results are "
    "intended for educational, spiritual, and entertainment purposes only and should "
    "not be considered professional legal, medical, financial, or psychological advice."
)
