"""Inhaled-dose estimates.

These are planning estimates from modelled concentrations and standard
breathing rates, not clinical doses. Every constant is exposed so the UI can
state the assumption it used.
"""

from __future__ import annotations

from typing import Literal

AgeBand = Literal["0-5", "6-12", "13-17", "18-59", "60+"]
Intensity = Literal["rest", "light", "moderate", "vigorous"]
Pathway = Literal[
    "walk",
    "cycle",
    "two_wheeler",
    "car",
    "bus",
    "train",
    "metro",
    "outdoor",
    "indoor",
]

INHALATION_RATES_M3_PER_H: dict[Intensity, float] = {
    "rest": 0.5,
    "light": 1.0,
    "moderate": 1.5,
    "vigorous": 2.4,
}

AGE_MULTIPLIERS: dict[AgeBand, float] = {
    "0-5": 1.2,
    "6-12": 1.1,
    "13-17": 1.0,
    "18-59": 1.0,
    "60+": 0.9,
}

INFILTRATION_FACTORS: dict[Pathway, float] = {
    "walk": 1.0,
    "cycle": 1.0,
    "two_wheeler": 1.0,
    "car": 0.5,
    "bus": 0.6,
    "train": 0.5,
    "metro": 0.3,
    "outdoor": 1.0,
    "indoor": 0.5,
}


def inhalation_rate_m3_per_h(intensity: Intensity, age_band: AgeBand) -> float:
    return INHALATION_RATES_M3_PER_H[intensity] * AGE_MULTIPLIERS[age_band]


def exposure_dose_ug(
    *,
    concentration_ug_m3: float,
    duration_min: int,
    intensity: Intensity,
    age_band: AgeBand,
    pathway: Pathway,
) -> float:
    if concentration_ug_m3 < 0:
        raise ValueError("Concentration cannot be negative.")
    if duration_min <= 0:
        raise ValueError("Duration must be positive.")
    hours = duration_min / 60.0
    return (
        concentration_ug_m3
        * inhalation_rate_m3_per_h(intensity, age_band)
        * INFILTRATION_FACTORS[pathway]
        * hours
    )


def relative_index(dose: float, baseline: float) -> int | None:
    if baseline <= 0:
        return None
    return round(dose / baseline * 100)
