"""House themes and position labels — EN/TA."""

HOUSE_THEMES = {
    1: {"en": "Self & vitality", "ta": "சுயம் / உயிர்சக்தி", "impacts_en": "health, confidence, life direction"},
    2: {"en": "Wealth & family", "ta": "செல்வம் / குடும்பம்", "impacts_en": "income, savings, family, speech"},
    3: {"en": "Courage & skills", "ta": "தைரியம் / திறன்", "impacts_en": "effort, siblings, communication, short travel"},
    4: {"en": "Home & happiness", "ta": "வீடு / சந்தோஷம்", "impacts_en": "property, mother, emotional peace, vehicles"},
    5: {"en": "Creativity & children", "ta": "படைப்பு / பிள்ளை", "impacts_en": "education, romance, speculation, children"},
    6: {"en": "Health & service", "ta": "ஆரோக்கியம் / சேவை", "impacts_en": "disease, debts, enemies, daily work"},
    7: {"en": "Partnership & marriage", "ta": "கூட்டாளர் / திருமணம்", "impacts_en": "spouse, contracts, public dealings"},
    8: {"en": "Transformation & longevity", "ta": "மாற்றம் / ஆயுள்", "impacts_en": "crisis, inheritance, research, occult"},
    9: {"en": "Fortune & dharma", "ta": "பாக்கியம் / தர்மம்", "impacts_en": "luck, father, spirituality, long travel"},
    10: {"en": "Career & status", "ta": "தொழில் / கர்மம்", "impacts_en": "profession, reputation, authority"},
    11: {"en": "Gains & networks", "ta": "லாபம் / நண்பர்கள்", "impacts_en": "profits, friends, aspirations, recovery"},
    12: {"en": "Loss & liberation", "ta": "இழப்பு / மோக்ஷம்", "impacts_en": "expenses, foreign lands, sleep, spirituality"},
}

POSITION_TYPE = {
    "own_house": {
        "en": "Lord in own house",
        "ta": "அதிபதி சொந்த வீட்டில்",
        "impact_en": "Natural strength and stability in this life area",
        "impact_ta": "இந்த துறையில் இயல்பான வலிமை",
    },
    "kendra_from_own": {
        "en": "Lord in Kendra from own",
        "ta": "அதிபதி கendra இல்",
        "impact_en": "Active involvement; results through action",
        "impact_ta": "சுறுசுறுப்பான ஈடுபாடு; செயல் வழி பலன்",
    },
    "trikona_from_own": {
        "en": "Lord in Trikona from own",
        "ta": "அதிபதி திரிகோணத்தில்",
        "impact_en": "Fortunate channel; dharmic support",
        "impact_ta": "அதிர்ஷ்ட வழி; தர்ம ஆதரவு",
    },
    "upachaya_from_own": {
        "en": "Lord in Upachaya from own",
        "ta": "அதிபதி உபசயத்தில்",
        "impact_en": "Grows with effort and time",
        "impact_ta": "முயற்சியுடன் காலப்போக்கில் வளரும்",
    },
    "dusthana_from_own": {
        "en": "Lord in Dusthana from own",
        "ta": "அதிபதி துஷ்டானத்தில்",
        "impact_en": "Challenging; extra care and timing needed",
        "impact_ta": "சவால்; கூ extra care மற்றும் சரியான காலம்",
    },
    "neutral_from_own": {
        "en": "Lord in neutral position from own",
        "ta": "அதிபதி நடுநிலை நிலை",
        "impact_en": "Moderate; mixed results",
        "impact_ta": "மிதமான; கலவையான பலன்கள்",
    },
}

KENDRA = frozenset({1, 4, 7, 10})
TRIKONA = frozenset({1, 5, 9})
UPACHAYA = frozenset({3, 6, 10, 11})
DUSTHANA = frozenset({6, 8, 12})

BENEFICS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
MALEFICS = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})

DISCLAIMER_EN = (
    "House Links map structural channels in the natal chart for prediction awareness. "
    "Combine with Dasa, transits, and divisional charts — not standalone advice."
)
DISCLAIMER_TA = (
    "வீட்டு தொடர்பு வரைபடம் ஜாதக கட்டமைப்பைக் காட்டுகிறது. "
    "தசை, கோசாரம், வர্গ கட்டங்களுடன் இணைத்துப் பார்க்கவும்."
)
