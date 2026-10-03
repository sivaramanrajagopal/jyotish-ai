"""
Parashara Shadbala for the seven planets.

Virupas follow the Prokerala / BPHS segmentation: Sthana, Dig, Kala,
Cheshta, Naisargika, and Drik. Rupas are the total divided by 60.
The ratio against each planet's required minimum is the strength reading.
Rahu and Ketu are outside classical Shadbala.
"""

from __future__ import annotations

import math
from datetime import datetime
from zoneinfo import ZoneInfo

import swisseph as swe_raw

import ephemeris as swe

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
TABLE_ORDER = ["Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]
SWE_ID = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
ENEMIES = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}
OWN = {
    "Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
    "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10},
}
# (sign index, degree from, degree to). End is exclusive except 30.
MOOLATRIKONA = {
    "Sun": (4, 0.0, 20.0),
    "Moon": (1, 4.0, 30.0),
    "Mars": (0, 0.0, 12.0),
    "Mercury": (5, 16.0, 20.0),
    "Jupiter": (8, 0.0, 10.0),
    "Venus": (6, 0.0, 15.0),
    "Saturn": (10, 0.0, 20.0),
}
DEBIL = {
    "Sun": 6 * 30 + 10, "Moon": 7 * 30 + 3, "Mars": 3 * 30 + 28,
    "Mercury": 11 * 30 + 15, "Jupiter": 9 * 30 + 5, "Venus": 5 * 30 + 27,
    "Saturn": 0 * 30 + 20,
}
RELATION_POINTS = {
    "adhimitra": 22.5, "friend": 15.0, "neutral": 7.5,
    "enemy": 3.75, "adhisatru": 1.875,
}
# 60 * n/7, rounded the way the reference sheet prints them.
NAISARGIKA = {
    "Sun": 60.0, "Moon": 51.43, "Venus": 42.85, "Jupiter": 34.28,
    "Mercury": 25.70, "Mars": 17.14, "Saturn": 8.57,
}
MINIMUM = {
    "Sun": 5.0, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0,
    "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0,
}
# Dig-bala house of full strength (1-based), measured from the ascendant degree.
DIG_HOUSE = {
    "Sun": 10, "Mars": 10, "Moon": 4, "Venus": 4,
    "Mercury": 1, "Jupiter": 1, "Saturn": 7,
}
WEEKDAY_LORD = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]
HORA_ORDER = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
# Ahargana remainder, index 0 = Tuesday. Matches the 1951 base used for Varsha/Masa.
ABDA_LORDS = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun", "Moon"]
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn"}

# Mean longitude at Ujjain, 1 Jan 1900, for Cheshta Bala.
_EPOCH_MEAN = {
    "Sun": 257.4568, "Mars": 270.22, "Mercury": 164.0,
    "Jupiter": 220.04, "Venus": 328.51, "Saturn": 236.74,
}
_EPOCH_SPEED = {
    "Sun": 0.9856, "Mars": 0.524, "Mercury": 4.0923,
    "Jupiter": 0.0831, "Venus": 1.60215, "Saturn": 0.033439,
}
# (sign, constant, yearly term)
_EPOCH_CORR = {
    "Sun": (1, 0.0, 0.0), "Mars": (1, 0.0, 0.0),
    "Mercury": (1, 6.67, -0.00133), "Jupiter": (-1, 3.3, 0.0067),
    "Venus": (-1, 5.0, 0.0001), "Saturn": (1, 5.0, 0.001),
}
_UJJAIN_LON = 76.0

BALA_ROWS = [
    ("uchcha", "Uchcha"),
    ("saptavargaja", "Saptavargaja"),
    ("ojayugma", "Ojhayugma"),
    ("kendradi", "Kendradi"),
    ("drekkana", "Drekkana"),
    ("sthana", "Sthaana"),
    ("dig", "Dig"),
    ("nathonnata", "Nathonnatha"),
    ("paksha", "Paksha"),
    ("tribhaga", "Tribhaga"),
    ("varsha", "Varsha"),
    ("masa", "Masa"),
    ("dina", "Dina"),
    ("hora", "Hora"),
    ("ayana", "Ayana"),
    ("yuddha", "Yuddha"),
    ("kala", "Kaala"),
    ("cheshta", "Cheshta"),
    ("naisargika", "Naisargika"),
    ("drik", "Drik"),
    ("total", "Total"),
    ("rupas", "Rupas"),
    ("minimum", "Minimum"),
    ("ratio", "Ratio"),
    ("rank", "Rank"),
    ("ishta", "Ishta Phala"),
    ("kashta", "Kashta Phala"),
]


def _r2(value: float) -> float:
    return round(float(value) + 1e-9, 2)


def _sign(lon: float) -> int:
    return int(lon / 30.0) % 12


def _in_moolatrikona(planet: str, lon: float) -> bool:
    sign, start, end = MOOLATRIKONA[planet]
    if _sign(lon) != sign:
        return False
    deg = lon % 30.0
    if end >= 30.0:
        return deg >= start
    return start <= deg < end


def _temp_friend(sign_a: int, sign_b: int) -> bool:
    """Planet in sign_b is a temporary friend of the planet in sign_a."""
    return ((sign_b - sign_a) % 12) in (1, 2, 3, 9, 10, 11)


def _compound(planet: str, owner: str, signs: dict[str, int]) -> str:
    if planet == owner:
        return "own"
    natural_friend = owner in FRIENDS[planet]
    natural_enemy = owner in ENEMIES[planet]
    temporary = _temp_friend(signs[planet], signs[owner])
    if natural_friend and temporary:
        return "adhimitra"
    if natural_friend or (natural_enemy and temporary):
        return "neutral"
    if natural_enemy:
        return "adhisatru"
    if temporary:
        return "friend"
    return "enemy"


def _hora_sign(lon: float) -> int:
    odd = _sign(lon) % 2 == 0
    first = (lon % 30.0) < 15.0
    if odd:
        return 4 if first else 3
    return 3 if first else 4


def _drekkana_sign(lon: float) -> int:
    return (_sign(lon) + int((lon % 30.0) // 10) * 4) % 12


def _saptamsa_sign(lon: float) -> int:
    part = int((lon % 30.0) // (30.0 / 7.0))
    sign = _sign(lon)
    if sign % 2 == 0:
        return (sign + part) % 12
    return (sign + 6 + part) % 12


def _navamsa_sign(lon: float) -> int:
    part = int((lon % 30.0) / (30.0 / 9.0))
    return ([0, 9, 6, 3][_sign(lon) % 4] + part) % 12


def _dwadasamsa_sign(lon: float) -> int:
    return (_sign(lon) + int((lon % 30.0) / 2.5)) % 12


def _trimsamsa_sign(lon: float) -> int:
    deg = lon % 30.0
    odd = [(5, 0), (10, 10), (18, 8), (25, 2), (30, 6)]
    even = [(5, 1), (12, 5), (20, 11), (25, 9), (30, 7)]
    table = odd if _sign(lon) % 2 == 0 else even
    for limit, sign in table:
        if deg < limit or limit == 30:
            return sign
    return table[-1][1]


def _varga_sign(kind: str, lon: float) -> int:
    return {
        "D1": _sign, "D2": _hora_sign, "D3": _drekkana_sign, "D7": _saptamsa_sign,
        "D9": _navamsa_sign, "D12": _dwadasamsa_sign, "D30": _trimsamsa_sign,
    }[kind](lon)


def _saptavargaja(planet: str, lon: float, signs: dict[str, int]) -> float:
    total = 0.0
    for kind in ("D1", "D2", "D3", "D7", "D9", "D12", "D30"):
        vsign = _varga_sign(kind, lon)
        if kind == "D1" and _in_moolatrikona(planet, lon):
            total += 45.0
        elif vsign in OWN[planet]:
            total += 30.0
        else:
            total += RELATION_POINTS[_compound(planet, SIGN_LORDS[vsign], signs)]
    return total


def _ojayugma(planet: str, lon: float) -> float:
    female = planet in ("Moon", "Venus")
    score = 0.0
    for sign in (_sign(lon), _navamsa_sign(lon)):
        even = sign % 2 == 1
        if female and even:
            score += 15.0
        if not female and not even:
            score += 15.0
    return score


def _kendradi(house: int) -> float:
    if house in (1, 4, 7, 10):
        return 60.0
    if house in (2, 5, 8, 11):
        return 30.0
    return 15.0


def _drekkana_bala(lon: float, planet: str) -> float:
    part = int((lon % 30.0) // 10.0)
    groups = (
        {"Sun", "Mars", "Jupiter"},
        {"Mercury", "Saturn"},
        {"Moon", "Venus"},
    )
    return 15.0 if planet in groups[min(part, 2)] else 0.0


def _uchcha(planet: str, lon: float) -> float:
    arc = (lon - DEBIL[planet]) % 360.0
    if arc > 180.0:
        arc = 360.0 - arc
    return arc / 3.0


def _dig(planet: str, lon: float, asc: float) -> float:
    power = (asc + (DIG_HOUSE[planet] - 1) * 30.0) % 360.0
    zero = (power + 180.0) % 360.0
    arc = abs((lon - zero + 180.0) % 360.0 - 180.0)
    return arc / 3.0


def _local_hour(moment: datetime) -> float:
    return moment.hour + moment.minute / 60.0 + moment.second / 3600.0


def _sun_event(jd_start: float, lat: float, lon: float, flag: int) -> datetime:
    _ret, tret = swe.rise_trans(jd_start, swe.SUN, flag, (lon, lat, 0.0), 0.0, 0.0)
    year, month, day, hour = swe.revjul(tret[0])
    whole = int(hour)
    minute = int((hour - whole) * 60)
    second = int(round(((hour - whole) * 60 - minute) * 60))
    if second >= 60:
        second -= 60
        minute += 1
    if minute >= 60:
        minute -= 60
        whole += 1
    return datetime(year, month, day, whole, minute, second, tzinfo=ZoneInfo("UTC"))


def _nathonnata(birth: datetime, lat: float, lon: float) -> dict[str, float]:
    """Day strength from apparent solar noon. Mercury is always 60."""
    local_midnight = birth.replace(hour=0, minute=0, second=0, microsecond=0)
    transit = _sun_event(_jd(local_midnight), lat, lon, swe_raw.CALC_MTRANSIT)
    hours_after_noon = (_jd(birth) - _jd(transit)) * 24.0
    from_midnight = (hours_after_noon + 12.0) % 24.0
    degrees = from_midnight * 15.0
    if degrees > 180.0:
        degrees = 360.0 - degrees
    day = degrees / 3.0
    night = (180.0 - degrees) / 3.0
    out = {planet: night for planet in ("Moon", "Mars", "Saturn")}
    out.update({planet: day for planet in ("Sun", "Jupiter", "Venus")})
    out["Mercury"] = 60.0
    return out


def _paksha(lons: dict[str, float], signs: dict[str, int]) -> dict[str, float]:
    gap = abs(lons["Moon"] - lons["Sun"]) % 360.0
    if gap > 180.0:
        gap = 360.0 - gap
    benefic_value = gap / 3.0
    malefic_value = 60.0 - benefic_value
    mercury_malefic = any(signs["Mercury"] == signs[other] for other in NATURAL_MALEFICS)
    out = {}
    for planet in PLANETS:
        malefic = planet in NATURAL_MALEFICS or (planet == "Mercury" and mercury_malefic)
        out[planet] = malefic_value if malefic else benefic_value
    out["Moon"] *= 2.0
    return out


def _tribhaga(birth: datetime, lat: float, lon: float) -> dict[str, float]:
    tz = birth.tzinfo or ZoneInfo("UTC")
    local_midnight = birth.replace(hour=0, minute=0, second=0, microsecond=0)
    jd0 = _jd(local_midnight)
    sunrise = _sun_event(jd0, lat, lon, swe_raw.CALC_RISE).astimezone(tz)
    sunset = _sun_event(jd0, lat, lon, swe_raw.CALC_SET).astimezone(tz)
    next_sunrise = _sun_event(jd0 + 1.0, lat, lon, swe_raw.CALC_RISE).astimezone(tz)
    out = {planet: 0.0 for planet in PLANETS}
    out["Jupiter"] = 60.0
    if sunrise <= birth < sunset:
        part = (sunset - sunrise).total_seconds() / 3.0
        elapsed = (birth - sunrise).total_seconds()
        lord = ("Mercury", "Sun", "Saturn")[min(2, int(elapsed // part))]
    else:
        if birth < sunrise:
            prev_set = _sun_event(jd0 - 1.0, lat, lon, swe_raw.CALC_SET).astimezone(tz)
            start, end = prev_set, sunrise
        else:
            start, end = sunset, next_sunrise
        part = (end - start).total_seconds() / 3.0
        elapsed = (birth - start).total_seconds()
        lord = ("Moon", "Venus", "Mars")[min(2, int(elapsed // part))]
    out[lord] = 60.0
    return out


def _ahargana_lords(jd: float) -> tuple[str, str]:
    year = swe.revjul(jd)[0]
    elapsed = int(jd - swe.julday(year, 1, 1, 0.0)) + 1
    total_years = (year - 1) - 1951
    leaps = len([
        y for y in range(1952, year)
        if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)
    ])
    ah = 174 + leaps * 366 + (total_years - leaps) * 365 + elapsed
    varsha = ABDA_LORDS[(int(ah // 360) * 3 + 1) % 7]
    masa = ABDA_LORDS[(int(ah // 30) * 2 + 1) % 7]
    return varsha, masa


def _dina_lord(birth: datetime, sunrise: datetime) -> str:
    from datetime import timedelta
    moment = birth if birth >= sunrise else birth - timedelta(days=1)
    return WEEKDAY_LORD[moment.weekday()]


def _hora_lord(birth: datetime, sunrise: datetime) -> str:
    from datetime import timedelta
    start = sunrise if birth >= sunrise else sunrise - timedelta(days=1)
    hours = max(0, int((birth - start).total_seconds() // 3600))
    begin = HORA_ORDER.index(WEEKDAY_LORD[start.weekday()])
    return HORA_ORDER[(begin + hours) % 7]


def _ayana(jd: float) -> dict[str, float]:
    obliquity = swe_raw.calc_ut(jd, swe_raw.ECL_NUT)[0][0]
    out = {}
    for planet, body in SWE_ID.items():
        tropical = swe.calc_ut(jd, body)[0][0]
        kranti = obliquity * math.sin(math.radians(tropical))
        # Moon and Saturn are strong in the south. Mercury is strong in both.
        if planet == "Mercury":
            kranti = abs(kranti)
        elif planet in ("Moon", "Saturn"):
            kranti = -kranti
        value = (24.0 + kranti) * 1.25
        if planet == "Sun":
            value *= 2.0
        out[planet] = value
    return out


def _mean_longitude(planet: str, jd: float, lon: float) -> float:
    epoch = _jd(datetime(1900, 1, 1, tzinfo=ZoneInfo("Asia/Kolkata")))
    days = jd - epoch + (_UJJAIN_LON - lon) / 15.0 / 24.0
    year = swe.revjul(jd)[0]
    sign, const, yearly = _EPOCH_CORR[planet]
    correction = sign * (const + yearly * (year - 1900))
    return (_EPOCH_MEAN[planet] + days * _EPOCH_SPEED[planet] + correction) % 360.0


def _cheshta(lons: dict[str, float], jd: float, lon: float) -> dict[str, float]:
    sun_mean = _mean_longitude("Sun", jd, lon)
    out = {planet: 0.0 for planet in PLANETS}
    for planet in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        mean = _mean_longitude(planet, jd, lon)
        if planet in ("Mercury", "Venus"):
            seegrocha, mean_used = mean, sun_mean
        else:
            seegrocha, mean_used = sun_mean, mean
        average = 0.5 * (lons[planet] + mean_used)
        diff = abs(seegrocha - average) % 360.0
        if diff > 180.0:
            diff = 360.0 - diff
        out[planet] = diff / 3.0
    return out


def _aspect_virupas(angle: float, aspecting: str) -> float:
    if angle < 30.0:
        value = 0.0
    elif angle < 60.0:
        value = 0.5 * (angle - 30.0)
    elif angle < 90.0:
        value = (angle - 60.0) + 15.0
    elif angle < 120.0:
        value = 0.5 * (120.0 - angle) + 30.0
    elif angle < 150.0:
        value = 150.0 - angle
    elif angle < 180.0:
        value = 2.0 * (angle - 150.0)
    elif angle < 300.0:
        value = 0.5 * (300.0 - angle)
    else:
        value = 0.0
    if aspecting == "Saturn" and 60.0 <= angle < 90.0:
        value += 45.0
    if aspecting == "Mars" and 90.0 <= angle < 120.0:
        value += 15.0
    if aspecting == "Jupiter" and 120.0 <= angle < 150.0:
        value += 30.0
    if aspecting == "Mars" and 210.0 <= angle < 240.0:
        value += 15.0
    if aspecting == "Jupiter" and 240.0 <= angle < 270.0:
        value += 30.0
    if aspecting == "Saturn" and 270.0 <= angle < 300.0:
        value += 45.0
    return value


def _drik(lons: dict[str, float], signs: dict[str, int]) -> dict[str, float]:
    mercury_malefic = any(signs["Mercury"] == signs[other] for other in NATURAL_MALEFICS)
    benefics = {"Jupiter", "Venus", "Moon"}
    if not mercury_malefic:
        benefics.add("Mercury")
    out = {}
    for aspected in PLANETS:
        plus = minus = 0.0
        for aspecting in PLANETS:
            angle = (360.0 + lons[aspected] - lons[aspecting]) % 360.0
            value = _aspect_virupas(angle, aspecting)
            if aspecting in benefics:
                plus += value
            else:
                minus += value
        out[aspected] = (plus - minus) / 4.0
    return out


def _yuddha(lons: dict[str, float]) -> dict[str, float]:
    """Planetary war. Sun and Moon do not enter. None within 1° gives zero."""
    out = {planet: 0.0 for planet in PLANETS}
    fighters = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    best = None
    for i, left in enumerate(fighters):
        for right in fighters[i + 1:]:
            gap = abs(lons[left] - lons[right]) % 360.0
            if gap > 180.0:
                gap = 360.0 - gap
            if gap < 1.0 and (best is None or gap < best[0]):
                best = (gap, left, right)
    if best is None:
        return out
    _gap, left, right = best
    # The planet with the greater Cheshta-ready longitude lead is not scored
    # here; a war this close contributes the gap itself, opposite in sign.
    out[left] = _r2(_gap * 30.0)
    out[right] = -out[left]
    return out


def _jd(moment: datetime) -> float:
    utc = moment.astimezone(ZoneInfo("UTC"))
    hour = utc.hour + utc.minute / 60.0 + utc.second / 3600.0 + utc.microsecond / 3.6e9
    return swe.julday(utc.year, utc.month, utc.day, hour)


def compute_shadbala(jd: float, lat: float, lon: float, birth: datetime) -> dict:
    """Return the seven planets, the ratio ranking, and every segmented bala."""
    lons = {}
    for planet, body in SWE_ID.items():
        lons[planet] = swe.calc_ut(jd, body, swe.FLG_SIDEREAL)[0][0] % 360.0
    asc = swe.houses_ex(jd, lat, lon, b"W", swe.FLG_SIDEREAL)[1][0] % 360.0
    signs = {planet: _sign(lon) for planet, lon in lons.items()}
    asc_sign = _sign(asc)
    houses = {planet: ((signs[planet] - asc_sign) % 12) + 1 for planet in PLANETS}

    tz = birth.tzinfo or ZoneInfo("UTC")
    local_midnight = birth.replace(hour=0, minute=0, second=0, microsecond=0)
    sunrise = _sun_event(_jd(local_midnight), lat, lon, swe_raw.CALC_RISE).astimezone(tz)

    uchcha = {p: _uchcha(p, lons[p]) for p in PLANETS}
    sapt = {p: _saptavargaja(p, lons[p], signs) for p in PLANETS}
    oja = {p: _ojayugma(p, lons[p]) for p in PLANETS}
    kendra = {p: _kendradi(houses[p]) for p in PLANETS}
    drekk = {p: _drekkana_bala(lons[p], p) for p in PLANETS}
    dig = {p: _dig(p, lons[p], asc) for p in PLANETS}
    natha = _nathonnata(birth, lat, lon)
    paksha = _paksha(lons, signs)
    tri = _tribhaga(birth, lat, lon)
    varsha_lord, masa_lord = _ahargana_lords(jd)
    dina = _dina_lord(birth, sunrise)
    hora = _hora_lord(birth, sunrise)
    ayana = _ayana(jd)
    cheshta = _cheshta(lons, jd, lon)
    drik = _drik(lons, signs)
    yuddha = _yuddha(lons)

    planets = []
    for planet in PLANETS:
        row = {
            "uchcha": _r2(uchcha[planet]),
            "saptavargaja": _r2(sapt[planet]),
            "ojayugma": _r2(oja[planet]),
            "kendradi": _r2(kendra[planet]),
            "drekkana": _r2(drekk[planet]),
            "dig": _r2(dig[planet]),
            "nathonnata": _r2(natha[planet]),
            "paksha": _r2(paksha[planet]),
            "tribhaga": _r2(tri[planet]),
            "varsha": 15.0 if planet == varsha_lord else 0.0,
            "masa": 30.0 if planet == masa_lord else 0.0,
            "dina": 45.0 if planet == dina else 0.0,
            "hora": 60.0 if planet == hora else 0.0,
            "ayana": _r2(ayana[planet]),
            "yuddha": _r2(yuddha[planet]),
            "cheshta": _r2(cheshta[planet]),
            "naisargika": NAISARGIKA[planet],
            "drik": _r2(drik[planet]),
        }
        row["sthana"] = _r2(sum(row[k] for k in ("uchcha", "saptavargaja", "ojayugma", "kendradi", "drekkana")))
        row["kala"] = _r2(sum(row[k] for k in (
            "nathonnata", "paksha", "tribhaga", "varsha", "masa", "dina", "hora", "ayana", "yuddha",
        )))
        row["total"] = _r2(sum(row[k] for k in ("sthana", "dig", "kala", "cheshta", "naisargika", "drik")))
        row["rupas"] = _r2(row["total"] / 60.0)
        row["minimum"] = MINIMUM[planet]
        row["ratio"] = _r2(row["rupas"] / row["minimum"])
        row["ishta"] = _r2(math.sqrt(max(row["uchcha"], 0.0) * max(row["cheshta"], 0.0)))
        row["kashta"] = _r2(math.sqrt(max(60.0 - row["uchcha"], 0.0) * max(60.0 - row["cheshta"], 0.0)))
        planets.append({"planet": planet, **row, "meets_minimum": row["ratio"] >= 1.0})

    ranked = sorted(planets, key=lambda item: (item["ratio"], item["rupas"]), reverse=True)
    for index, item in enumerate(ranked, start=1):
        item["rank"] = index

    return {
        "planets": ranked,
        "table_order": TABLE_ORDER,
        "rows": [{"key": key, "label": label} for key, label in BALA_ROWS],
        "varsha_lord": varsha_lord,
        "masa_lord": masa_lord,
        "dina_lord": dina,
        "hora_lord": hora,
        "note": (
            "Ratio is rupas divided by the classical minimum. "
            "A value of 1 has met that minimum. "
            "Ishta and Kashta describe comfort and strain. They do not change the rank."
        ),
    }
