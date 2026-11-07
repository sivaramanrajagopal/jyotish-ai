"""Life themes and the houses that carry them (Parashari).

A theme is switched on by its key houses. Support houses are listed for the reader;
they do not switch a theme on by themselves, so one bhukti does not light every theme.
"""

THEMES = [
    {
        "key": "career",
        "en": "Career & status", "ta": "தொழில் / அந்தஸ்து",
        "key_houses": [10], "support": [2, 6, 11],
    },
    {
        "key": "wealth",
        "en": "Income & wealth", "ta": "வருமானம் / செல்வம்",
        "key_houses": [2, 11], "support": [5, 9],
    },
    {
        "key": "marriage",
        "en": "Marriage & partnership", "ta": "திருமணம் / கூட்டு",
        "married_en": "Spouse & partnership", "married_ta": "வாழ்க்கைத் துணை / கூட்டு",
        "key_houses": [7], "support": [2, 11],
        "min_age": 18,
    },
    {
        "key": "children",
        "en": "Children", "ta": "குழந்தைகள்",
        "key_houses": [5], "support": [9, 11],
        "min_age": 18,
    },
    {
        "key": "property",
        "en": "Home & property", "ta": "வீடு / சொத்து",
        "key_houses": [4], "support": [2, 11],
    },
    {
        "key": "health",
        "en": "Health & care", "ta": "ஆரோக்கியம் / கவனம்",
        "key_houses": [1, 6, 8, 12], "support": [],
        "care": True,
    },
    {
        "key": "foreign",
        "en": "Foreign & travel", "ta": "வெளிநாடு / பயணம்",
        "key_houses": [12, 9], "support": [3, 7],
    },
    {
        "key": "education",
        "en": "Education", "ta": "கல்வி",
        "key_houses": [4, 5], "support": [9],
        "max_age": 30,
    },
]

MARRIED_NOTE_EN = "Already married: the 7th reads as the spouse, partnerships and contracts."
MARRIED_NOTE_TA = "திருமணம் ஆனவர்: 7ஆம் வீடு வாழ்க்கைத் துணை, கூட்டு, ஒப்பந்தங்களைக் காட்டும்."
CARE_NOTE_EN = "A care theme: when it is on, give the body rest and attention."
CARE_NOTE_TA = "கவனத்துக்குரிய பகுதி: செயலில் இருக்கும்போது உடல்நலத்தில் கவனம்."
