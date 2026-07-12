"""Shared constants for Life Cycle Simulator."""

KARAKA_ROLES = {
    "Sun": "Authority / father / government",
    "Moon": "Mind / mother / public",
    "Mars": "Courage / surgery / property",
    "Mercury": "Intellect / commerce / education",
    "Jupiter": "Wisdom / guru / children / fortune",
    "Venus": "Marriage / luxury / arts",
    "Saturn": "Karma / service / longevity",
    "Rahu": "Foreign / unconventional / sudden",
    "Ketu": "Spirituality / detachment / surgery",
}

LIFE_THEMES = [
    {"key": "marriage", "label": "Marriage & partnership", "houses": [2, 7, 11], "karakas": ["Venus", "Jupiter"]},
    {"key": "career", "label": "Career & status", "houses": [6, 10, 11], "karakas": ["Sun", "Saturn", "Mercury"]},
    {"key": "health", "label": "Health & service", "houses": [6, 8, 12], "karakas": ["Mars", "Saturn", "Moon"]},
    {"key": "property", "label": "Home & property", "houses": [4, 11], "karakas": ["Mars", "Venus", "Moon"]},
    {"key": "foreign", "label": "Foreign & travel", "houses": [9, 12], "karakas": ["Rahu", "Moon", "Saturn"]},
    {"key": "education", "label": "Education & merit", "houses": [4, 5, 9], "karakas": ["Mercury", "Jupiter"]},
]

SLOW_TRANSIT_PLANETS = ("Jupiter", "Saturn", "Mars", "Rahu")
PLANET_WEIGHT = {"Jupiter": 4, "Saturn": 4, "Rahu": 3, "Mars": 2}
