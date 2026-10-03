"""
Classical remedial suggestions from a planet's Sthula / Sukshma / condition score.

One branch per planet, in this order:
  1. Condition score >= 80 → no intervention
  2. Vikala or Kala → bija mantra + deity; no gemstone
  3. Peeda, Peethya, or Deena → charity + weekday fast + deity
  4. Nidra or Sayana → mantra + charity; gem only if a functional benefic
  5. Otherwise → no specific remedy from these rules

Affliction wins over a dormant Sukshma state, so a Deena+Nidra planet
does not receive a gemstone.

Functional benefic (gem gate only), whole-sign houses from the lagna:
  - Yogakaraka (owns a kendra 4/7/10 and a trikona 5/9), or
  - Lagna lord that does not also own 6, 8, or 12, or
  - Lord of 5 or 9.
  A natural malefic who also owns the 8th is excluded.
  A natural benefic who owns 5 or 9 stays eligible even with an 8th co-lordship.
  Rahu and Ketu own no signs, so they are never gem-eligible.
"""

from __future__ import annotations

from typing import Any, Literal

from agents.natal_agent import SIGN_LORDS, SIGNS

PlanetName = Literal[
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"
]

RemedyBranch = Literal["peak", "combust_weak", "afflicted", "dormant", "none"]

NATURAL_BENEFICS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
DORMANT_SUKSHMA = frozenset({"Nidra", "Sayana"})
AFFLICTED_STHULA = frozenset({"Peeda", "Peethya", "Deena"})
COMBUST_WEAK_STHULA = frozenset({"Vikala", "Kala"})
KENDRA = frozenset({4, 7, 10})
TRIKONA = frozenset({5, 9})
DUSTHANA = frozenset({6, 8, 12})

_NOTE = (
    "Classical suggestion from this planet’s avastha, not a prescription. "
    "108 recitations is the count shown here; a longer anusthana can be done "
    "in the planet’s hora or during its dasha. "
    "Gemstones are withheld for combust, debilitated, and functional malefic planets."
)

_NOTE_TA = (
    "இது அவஸ்தாவின் அடிப்படையிலான பாரம்பரிய பரிந்துரை; மருத்துவ அல்லது கட்டாய ஆலோசனை அல்ல. "
    "ஜபம் 108 முறை. அதிக அனுஷ்டானம் கிரக ஹோரையிலோ தசாவிலோ செய்யலாம்."
)

# Bija, deity, dana, vrata, ratna. Tamil lines are recital transliterations.
REMEDY_MAP: dict[str, dict[str, Any]] = {
    "Sun": {
        "bija_mantra": "Om Hram Hreem Hroum Sah Suryaya Namah",
        "bija_mantra_ta": "ஓம் ஹ்ராம் ஹ்ரீம் ஹ்ரௌம் ஸஹ சூர்யாய நமஹ",
        "mantra_count": 108,
        "deity": "Lord Shiva / Surya Narayana",
        "deity_ta": "சிவபெருமான் / சூரிய நாராயணர்",
        "charity_items": ["Wheat", "Jaggery", "Copper", "Red cloth"],
        "charity_items_ta": ["கோதுமை", "வெல்லம்", "செம்பு", "சிவப்புத் துணி"],
        "fast_day": "Sunday",
        "fast_day_ta": "ஞாயிற்றுக்கிழமை",
        "gemstone": "Ruby",
        "gemstone_ta": "மாணிக்கம்",
    },
    "Moon": {
        "bija_mantra": "Om Shram Shreem Shroum Sah Chandramase Namah",
        "bija_mantra_ta": "ஓம் ஸ்ராம் ஸ்ரீம் ஸ்ரௌம் ஸஹ சந்த்ரமஸே நமஹ",
        "mantra_count": 108,
        "deity": "Goddess Parvati / Lord Shiva",
        "deity_ta": "பார்வதி / சிவபெருமான்",
        "charity_items": ["Rice", "Milk", "White cloth"],
        "charity_items_ta": ["அரிசி", "பால்", "வெள்ளைத் துணி"],
        "fast_day": "Monday",
        "fast_day_ta": "திங்கட்கிழமை",
        "gemstone": "Pearl",
        "gemstone_ta": "முத்து",
    },
    "Mars": {
        "bija_mantra": "Om Kram Kreem Kroum Sah Bhaumaya Namah",
        "bija_mantra_ta": "ஓம் க்ராம் க்ரீம் க்ரௌம் ஸஹ பௌமாய நமஹ",
        "mantra_count": 108,
        "deity": "Lord Subrahmanya (Murugan) / Hanuman",
        "deity_ta": "முருகன் / அனுமான்",
        "charity_items": ["Red lentils (masoor dal)", "Copper vessels", "Land-related service"],
        "charity_items_ta": ["மசூர் பருப்பு", "செப்பு பாத்திரம்", "நிலத் தொண்டு"],
        "fast_day": "Tuesday",
        "fast_day_ta": "செவ்வாய்க்கிழமை",
        "gemstone": "Red coral",
        "gemstone_ta": "பவளம்",
    },
    "Mercury": {
        "bija_mantra": "Om Bram Breem Broum Sah Budhaya Namah",
        "bija_mantra_ta": "ஓம் ப்ராம் ப்ரீம் ப்ரௌம் ஸஹ புதாய நமஹ",
        "mantra_count": 108,
        "deity": "Lord Vishnu",
        "deity_ta": "விஷ்ணு",
        "charity_items": ["Green gram", "Books", "Support for students"],
        "charity_items_ta": ["பச்சைப் பயறு", "புத்தகங்கள்", "மாணவர் உதவி"],
        "fast_day": "Wednesday",
        "fast_day_ta": "புதன்கிழமை",
        "gemstone": "Emerald",
        "gemstone_ta": "மரகதம்",
    },
    "Jupiter": {
        "bija_mantra": "Om Gram Greem Groum Sah Gurave Namah",
        "bija_mantra_ta": "ஓம் கிராம் கிரீம் கிரௌம் ஸஹ குரவே நமஹ",
        "mantra_count": 108,
        "deity": "Lord Dakshinamurthy / Lord Brahma",
        "deity_ta": "தட்சிணாமூர்த்தி / பிரம்மா",
        "charity_items": ["Turmeric", "Yellow cloth", "Teaching or feeding support"],
        "charity_items_ta": ["மஞ்சள்", "மஞ்சள் ஆடை", "கற்பித்தல் அல்லது அன்னதானம்"],
        "fast_day": "Thursday",
        "fast_day_ta": "வியாழக்கிழமை",
        "gemstone": "Yellow sapphire",
        "gemstone_ta": "புஷ்பராகம்",
    },
    "Venus": {
        "bija_mantra": "Om Dram Dreem Droum Sah Shukraya Namah",
        "bija_mantra_ta": "ஓம் த்ராம் த்ரீம் த்ரௌம் ஸஹ சுக்ராய நமஹ",
        "mantra_count": 108,
        "deity": "Goddess Lakshmi",
        "deity_ta": "லட்சுமி",
        "charity_items": ["White rice", "Ghee", "Silk clothing", "Support for women’s welfare"],
        "charity_items_ta": ["வெள்ளை அரிசி", "நெய்", "பட்டு ஆடை", "பெண்கள் நல உதவி"],
        "fast_day": "Friday",
        "fast_day_ta": "வெள்ளிக்கிழமை",
        "gemstone": "Diamond",
        "gemstone_ta": "வைரம்",
    },
    "Saturn": {
        "bija_mantra": "Om Pram Preem Proum Sah Shanaischaraya Namah",
        "bija_mantra_ta": "ஓம் ப்ராம் ப்ரீம் ப்ரௌம் ஸஹ சனைச்சராய நமஹ",
        "mantra_count": 108,
        "deity": "Lord Hanuman / Lord Yama",
        "deity_ta": "அனுமான் / யமன்",
        "charity_items": ["Black sesame", "Mustard oil", "Iron items", "Service to labourers"],
        "charity_items_ta": ["எள்", "கடுகு எண்ணெய்", "இரும்புப் பொருள்", "உழைப்பாளருக்கு சேவை"],
        "fast_day": "Saturday",
        "fast_day_ta": "சனிக்கிழமை",
        "gemstone": "Blue sapphire",
        "gemstone_ta": "நீலக்கல்",
    },
    "Rahu": {
        "bija_mantra": "Om Bhram Bhreem Bhroum Sah Rahave Namah",
        "bija_mantra_ta": "ஓம் ப்ராம் ப்ரீம் ப்ரௌம் ஸஹ ராஹவே நமஹ",
        "mantra_count": 108,
        "deity": "Goddess Durga",
        "deity_ta": "துர்கை",
        "charity_items": ["Sesame", "Coconut", "Blanket", "Help to those in need"],
        "charity_items_ta": ["எள்", "தேங்காய்", "கம்பளி", "ஏழைகளுக்கு உதவி"],
        "fast_day": "Saturday",
        "fast_day_ta": "சனிக்கிழமை",
        "gemstone": "Hessonite (gomed)",
        "gemstone_ta": "கோமேதகம்",
    },
    "Ketu": {
        "bija_mantra": "Om Stram Streem Stroum Sah Ketave Namah",
        "bija_mantra_ta": "ஓம் ஸ்ராம் ஸ்ரீம் ஸ்ரௌம் ஸஹ கேதவே நமஹ",
        "mantra_count": 108,
        "deity": "Lord Ganesha",
        "deity_ta": "விநாயகர்",
        "charity_items": ["Sesame", "Blanket", "Multi-coloured cloth", "Ganesha temple seva"],
        "charity_items_ta": ["எள்", "கம்பளி", "பல நிறத் துணி", "விநாயகர் ஆலய சேவை"],
        "fast_day": "Tuesday",
        "fast_day_ta": "செவ்வாய்க்கிழமை",
        "gemstone": "Cat's eye",
        "gemstone_ta": "வைடூரியம்",
    },
}


def houses_owned(planet: str, lagna_rasi_index: int) -> set[int]:
    """Whole-sign houses (1–12) this planet rules for the given lagna (1 = Aries)."""
    lagna_idx0 = int(lagna_rasi_index) - 1
    owned: set[int] = set()
    for house in range(1, 13):
        sign = SIGNS[(lagna_idx0 + house - 1) % 12]
        if SIGN_LORDS.get(sign) == planet:
            owned.add(house)
    return owned


def is_functional_benefic(planet: str, lagna_rasi_index: int) -> bool:
    """True when a dormant planet may be offered its gemstone."""
    houses = houses_owned(planet, lagna_rasi_index)
    if not houses:
        return False
    trikona = bool(houses & TRIKONA)
    yogakaraka = trikona and bool(houses & KENDRA)
    if yogakaraka:
        return True
    if 1 in houses and not (houses & DUSTHANA):
        return True
    if trikona and 8 in houses and planet not in NATURAL_BENEFICS:
        return False
    return trikona


def _item(kind: str, label: str, text: str, text_ta: str, detail: str = "") -> dict[str, str]:
    row = {"kind": kind, "label": label, "text": text, "text_ta": text_ta}
    if detail:
        row["detail"] = detail
    return row


def _mantra_item(mapping: dict[str, Any]) -> dict[str, str]:
    count = int(mapping["mantra_count"])
    return _item(
        "mantra",
        "Mantra japa",
        mapping["bija_mantra"],
        mapping["bija_mantra_ta"],
        f"{count} times",
    )


def _deity_item(mapping: dict[str, Any]) -> dict[str, str]:
    return _item("deity", "Deity worship", mapping["deity"], mapping["deity_ta"])


def _charity_item(mapping: dict[str, Any]) -> dict[str, str]:
    return _item(
        "charity",
        "Charity",
        ", ".join(mapping["charity_items"]),
        ", ".join(mapping["charity_items_ta"]),
    )


def _fast_item(mapping: dict[str, Any]) -> dict[str, str]:
    return _item(
        "fast",
        "Weekday fast",
        mapping["fast_day"],
        mapping["fast_day_ta"],
    )


def _gem_item(mapping: dict[str, Any]) -> dict[str, str]:
    return _item(
        "gem",
        "Gemstone",
        mapping["gemstone"],
        mapping["gemstone_ta"],
        "Only while this planet is a functional benefic and not combust or debilitated",
    )


def get_remedies_for_planet(
    planet_name: str,
    sthula_name: str,
    sukshma_name: str,
    net_score: float,
    *,
    functional_benefic: bool,
) -> dict[str, Any]:
    """Pick one remedial branch from the combined avastha result."""
    mapping = REMEDY_MAP[planet_name]
    net = float(net_score)
    items: list[dict[str, str]] = []
    cautions: list[str] = []

    if net >= 80.0:
        branch: RemedyBranch = "peak"
        objective = "Planet operating at peak efficiency."
        objective_ta = "கிரகம் உச்ச செயல்திறனில் இயங்குகிறது."
        approach = "No remedial intervention from these rules."
    elif sthula_name in COMBUST_WEAK_STHULA:
        branch = "combust_weak"
        objective = "To restore visibility and vital vitality."
        objective_ta = "ஒளியையும் உயிர்த்தன்மையையும் மீட்ட."
        approach = "Bija mantra and deity worship. Gemstone is avoided."
        items = [_mantra_item(mapping), _deity_item(mapping)]
        cautions.append("Gemstone avoided for a combust or debilitated planet.")
    elif sthula_name in AFFLICTED_STHULA:
        branch = "afflicted"
        objective = "To calm affliction and ease friction."
        objective_ta = "பாதிப்பைத் தணித்து உரசலைக் குறைக்க."
        approach = "Charity, a weekday fast, and deity worship."
        items = [_charity_item(mapping), _fast_item(mapping), _deity_item(mapping)]
        if sukshma_name in DORMANT_SUKSHMA:
            cautions.append(
                "Sukshma is dormant as well; the afflicted Sthula remedy is used, without a gemstone."
            )
    elif sukshma_name in DORMANT_SUKSHMA:
        branch = "dormant"
        objective = "To awaken the planet’s operational drive."
        objective_ta = "கிரகத்தின் செயல்பாட்டைத் தூண்ட."
        approach = "Mantra japa and charity."
        items = [_mantra_item(mapping), _charity_item(mapping)]
        if functional_benefic:
            approach = "Mantra japa, charity, and a gemstone — this planet is a functional benefic for the lagna."
            items.append(_gem_item(mapping))
        else:
            cautions.append("Gemstone not suggested — this planet is not a functional benefic for the lagna.")
    else:
        branch = "none"
        objective = "No specific remedy from these rules."
        objective_ta = "இந்த விதிகளின்படி தனிப் பரிகாரம் இல்லை."
        approach = "Capacity and efficiency do not fall into the remedial branches."

    return {
        "planet": planet_name,
        "branch": branch,
        "sthula": sthula_name,
        "sukshma": sukshma_name,
        "net": round(net, 2),
        "functional_benefic": bool(functional_benefic),
        "intervention": branch not in ("peak", "none"),
        "objective": objective,
        "objective_ta": objective_ta,
        "approach": approach,
        "items": items,
        "cautions": cautions,
        "note": _NOTE,
        "note_ta": _NOTE_TA,
        "mantra_count": int(mapping["mantra_count"]),
    }
