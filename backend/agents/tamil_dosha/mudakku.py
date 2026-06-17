"""Mudakku Rasi — two competing Tamil methods (display both, never merge)."""

from __future__ import annotations

from .constants import CONFIDENCE_MEDIUM, CONFIDENCE_UNVERIFIED
from .utils import house_from_rasi, nakshatra_label, rasi_label, rasi_of_nakshatra_pada


def compute_mudakku_method_a(
    *,
    moon_rasi_index: int,
    sun_rasi_index: int,
    lagna_rasi_index: int,
) -> dict:
    n = ((int(moon_rasi_index) - int(sun_rasi_index)) % 12) + 1
    mudakku_rasi_index = (int(lagna_rasi_index) + n - 1) % 12
    return {
        "label": "Method A (Unverified — no primary source located)",
        "how_calculated": (
            "N = ((Moon rasi − Sun rasi) mod 12) + 1; "
            "Mudakku rasi = Lagna + N − 1 (mod 12); house = N from Lagna."
        ),
        "n_value": n,
        "rasi": rasi_label(mudakku_rasi_index),
        "house": n,
        "confidence": CONFIDENCE_UNVERIFIED,
        "source_note": "Formula documented in practitioner notes only; no primary classical source located during audit.",
    }


def compute_mudakku_method_b(
    *,
    sun_nakshatra_index: int,
    sun_nakshatra_pada: int,
    lagna_rasi_index: int,
) -> dict:
    moola_index = 18
    purva_ashadha_index = 19
    n = ((moola_index - int(sun_nakshatra_index)) % 27) + 1
    mudakku_nak_idx = (purva_ashadha_index + n - 1) % 27
    mudakku_rasi_index = rasi_of_nakshatra_pada(mudakku_nak_idx, int(sun_nakshatra_pada))
    return {
        "label": "Method B (Tamil practitioner tradition)",
        "how_calculated": (
            "N = ((Moola nakshatra − Sun nakshatra) mod 27) + 1; "
            "anchor Purva Ashadha + N − 1; rasi from nakshatra+pada "
            "(pada taken from Sun — engineering assumption, flagged)."
        ),
        "n_value": n,
        "nakshatra": nakshatra_label(mudakku_nak_idx),
        "pada": int(sun_nakshatra_pada),
        "assumption_flags": ["pada_from_sun"],
        "rasi": rasi_label(mudakku_rasi_index),
        "house": house_from_rasi(mudakku_rasi_index, lagna_rasi_index),
        "confidence": CONFIDENCE_MEDIUM,
        "source_note": "Tamil practitioner tradition; pada linkage to Sun is an implementation assumption.",
    }


def compute_mudakku(
    *,
    moon_rasi_index: int,
    sun_rasi_index: int,
    sun_nakshatra_index: int,
    sun_nakshatra_pada: int,
    lagna_rasi_index: int,
) -> dict:
    method_a = compute_mudakku_method_a(
        moon_rasi_index=moon_rasi_index,
        sun_rasi_index=sun_rasi_index,
        lagna_rasi_index=lagna_rasi_index,
    )
    method_b = compute_mudakku_method_b(
        sun_nakshatra_index=sun_nakshatra_index,
        sun_nakshatra_pada=sun_nakshatra_pada,
        lagna_rasi_index=lagna_rasi_index,
    )
    disagree = method_a["rasi"]["index"] != method_b["rasi"]["index"]
    return {
        "methods_disagree": disagree,
        "method_a": method_a,
        "method_b": method_b,
    }
