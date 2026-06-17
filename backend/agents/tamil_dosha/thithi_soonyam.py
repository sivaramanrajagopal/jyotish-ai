"""Thithi Soonyam (Dagdha Rasi) — natal void signs for birth tithi."""

from __future__ import annotations

from .constants import CONFIDENCE_MEDIUM, SHASHTI_VARIANTS, TITHI_SOONYA_TABLE
from .utils import house_from_rasi, rasi_label, tithi_index_from_longitudes


SOURCE_NOTE = (
    "Cross-verified across independent regional panchanga compilations. "
    "Natal (birth-chart) application has no single traceable classical source; "
    "distinct from the related muhurta-only Dagdha Tithi transit rule."
)


def compute_thithi_soonyam(
    *,
    moon_lon: float,
    sun_lon: float,
    lagna_rasi_index: int,
    shashti_variant: str = "mesha_simha",
    planet_positions: dict | None = None,
) -> dict:
    tithi_index, tithi_name, paksha = tithi_index_from_longitudes(moon_lon, sun_lon)

    dagdha_indices = list(TITHI_SOONYA_TABLE.get(tithi_index, []))
    if tithi_index == 6:
        dagdha_indices = list(SHASHTI_VARIANTS.get(shashti_variant, SHASHTI_VARIANTS["mesha_simha"]))

    dagdha_rasis = [rasi_label(i) for i in dagdha_indices]
    affected_houses = [house_from_rasi(i, lagna_rasi_index) for i in dagdha_indices]

    planets_in_dagdha = []
    if planet_positions:
        dagdha_set = set(dagdha_indices)
        for pname, pdata in planet_positions.items():
            if pname in ("Rahu", "Ketu"):
                continue
            si = pdata.get("sign_index")
            if si is not None and si in dagdha_set:
                planets_in_dagdha.append({
                    "planet": pname,
                    "sign": pdata.get("sign"),
                    "house": pdata.get("house"),
                })

    return {
        "tithi_index": tithi_index,
        "tithi_name": tithi_name,
        "paksha": paksha,
        "shashti_variant": shashti_variant if tithi_index == 6 else None,
        "dagdha_rasis": dagdha_rasis,
        "affected_houses": affected_houses,
        "planets_in_dagdha": planets_in_dagdha,
        "confidence": CONFIDENCE_MEDIUM,
        "source_note": SOURCE_NOTE,
    }
