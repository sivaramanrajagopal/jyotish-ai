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
    "lost_and_found": 4,
    "competitive_exam": 6,
    "key_interest": 11,
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
    "lost_and_found": "Lost & Found",
    "competitive_exam": "Competitive Exam",
    "key_interest": "Key Areas of Interest",
}

CATEGORY_ICONS: dict[str, str] = {
    "career": "🏆",
    "marriage": "💑",
    "money": "💰",
    "property": "🏠",
    "health": "⚕️",
    "travel": "✈️",
    "education": "📚",
    "general": "🔮",
    "lost_and_found": "🔍",
    "competitive_exam": "📝",
    "key_interest": "⭐",
}

# Pre-defined horary questions per category (dropdown — no free-text required)
CATEGORY_QUESTIONS: dict[str, list[dict[str, str]]] = {
    "career": [
        {"id": "promotion", "text": "Will I get a promotion soon?"},
        {"id": "job_offer", "text": "Will I receive a job offer?"},
        {"id": "job_change", "text": "Is changing jobs favourable now?"},
        {"id": "business", "text": "Will my business venture succeed?"},
    ],
    "marriage": [
        {"id": "marriage_soon", "text": "Will marriage happen soon?"},
        {"id": "relationship", "text": "Is this relationship favourable?"},
        {"id": "reconcile", "text": "Will reconciliation with my partner occur?"},
        {"id": "proposal", "text": "Will a proposal be accepted?"},
    ],
    "money": [
        {"id": "financial_gain", "text": "Will I gain financially soon?"},
        {"id": "loan", "text": "Will I get the loan or funding I need?"},
        {"id": "investment", "text": "Is this investment favourable?"},
        {"id": "debt", "text": "Will I overcome financial difficulty?"},
    ],
    "property": [
        {"id": "buy_property", "text": "Will I buy property successfully?"},
        {"id": "sell_property", "text": "Will I sell my property favourably?"},
        {"id": "vehicle", "text": "Will I acquire a vehicle soon?"},
    ],
    "health": [
        {"id": "recovery", "text": "Will recovery from illness occur?"},
        {"id": "treatment", "text": "Will the treatment be effective?"},
        {"id": "surgery", "text": "Is surgery advisable and favourable?"},
    ],
    "travel": [
        {"id": "travel_abroad", "text": "Will foreign travel materialise?"},
        {"id": "trip_safe", "text": "Will my journey be safe and successful?"},
        {"id": "visa", "text": "Will visa or travel approval come through?"},
    ],
    "education": [
        {"id": "admission", "text": "Will I get admission to the desired course?"},
        {"id": "exam_pass", "text": "Will I pass the upcoming exam?"},
        {"id": "scholarship", "text": "Will I receive a scholarship or grant?"},
    ],
    "general": [
        {"id": "overall", "text": "Is the overall outlook favourable now?"},
        {"id": "wish", "text": "Will my current wish be fulfilled?"},
        {"id": "obstacle", "text": "Will the main obstacle be removed?"},
    ],
    "lost_and_found": [
        {"id": "recover_lost", "text": "Will I recover my lost item?"},
        {"id": "still_findable", "text": "Is the lost article still findable?"},
        {"id": "where_direction", "text": "Is recovery of the lost object indicated?"},
        {"id": "stolen", "text": "If stolen, is return of the item possible?"},
    ],
    "competitive_exam": [
        {"id": "pass_exam", "text": "Will I pass the competitive exam?"},
        {"id": "get_selected", "text": "Will I get selected in the exam?"},
        {"id": "rank", "text": "Will I achieve a good rank or score?"},
        {"id": "interview", "text": "Will the interview stage be successful?"},
    ],
    "key_interest": [
        {"id": "h1_self", "text": "H1 Self — Is my health and vitality favourable now?"},
        {"id": "h2_wealth", "text": "H2 Wealth — Is financial gain indicated now?"},
        {"id": "h3_courage", "text": "H3 Courage — Are communication and efforts supported?"},
        {"id": "h4_home", "text": "H4 Home — Is home and property matter favourable?"},
        {"id": "h5_education", "text": "H5 Education — Are creativity and studies favoured?"},
        {"id": "h6_health", "text": "H6 Health — Can I overcome illness or competition?"},
        {"id": "h7_marriage", "text": "H7 Marriage — Is partnership favourable now?"},
        {"id": "h8_obstacles", "text": "H8 Obstacles — Will sudden blockages resolve?"},
        {"id": "h9_fortune", "text": "H9 Fortune — Is luck and dharma on my side?"},
        {"id": "h10_career", "text": "H10 Career — Is professional success indicated?"},
        {"id": "h11_gains", "text": "H11 Gains — Will wishes and income manifest?"},
        {"id": "h12_spiritual", "text": "H12 Spiritual — Is foreign or spiritual path favourable?"},
        {"id": "most_favourable", "text": "Which life area looks most favourable overall?"},
    ],
}


KEY_INTEREST_HOUSE: dict[str, int] = {
    "h1_self": 1,
    "h2_wealth": 2,
    "h3_courage": 3,
    "h4_home": 4,
    "h5_education": 5,
    "h6_health": 6,
    "h7_marriage": 7,
    "h8_obstacles": 8,
    "h9_fortune": 9,
    "h10_career": 10,
    "h11_gains": 11,
    "h12_spiritual": 12,
    "most_favourable": 11,
}


def resolve_question(category: str, question_id: str | None, question_text: str | None) -> tuple[str, str]:
    """Return (question_id, question_text) from id or explicit text."""
    cat = category.lower().strip()
    questions = CATEGORY_QUESTIONS.get(cat, [])
    if question_id:
        for q in questions:
            if q["id"] == question_id:
                return q["id"], q["text"]
        raise ValueError(f"Unknown question_id '{question_id}' for category '{cat}'.")
    text = (question_text or "").strip()
    if text:
        return question_id or "custom", text
    if questions:
        return questions[0]["id"], questions[0]["text"]
    raise ValueError("A question must be selected.")

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
