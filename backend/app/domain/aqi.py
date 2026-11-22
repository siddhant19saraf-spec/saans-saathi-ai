"""CPCB 2014 National Air Quality Index.

The official method is explicit about averaging windows and completeness:

* PM2.5, PM10, NO2 and SO2 use 24-hour averages; CO and O3 use 8-hour averages.
* A sub-index is only computed when at least 75% of the window is present
  (16 of 24 hours, 6 of 8 hours).
* The overall AQI is the worst sub-index and requires at least three
  pollutants, necessarily including PM2.5 or PM10.
* An 8-hour ozone mean above 208 µg/m³ is replaced by the latest 1-hour value.

A single hourly value is never treated as a 24-hour mean. Callers either pass
pre-computed :class:`AveragingInfo` records or use :func:`rolling_averages` on
an hourly series.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

Pollutant = Literal[
    "pm2_5",
    "pm10",
    "no2_ug_m3",
    "so2_ug_m3",
    "co_ug_m3",
    "o3_ug_m3",
]

# (category upper concentration, category upper index). The lower index for a
# band is the previous band's upper index, which reproduces the documented
# worked examples (PM2.5 75.2 -> 150.7 -> 151, 150 -> 323, 45 -> 75).
_BREAKPOINTS: dict[Pollutant, tuple[tuple[float, int], ...]] = {
    "pm2_5": (
        (30.0, 50),
        (60.0, 100),
        (90.0, 200),
        (120.0, 300),
        (250.0, 400),
        (500.0, 500),
    ),
    "pm10": (
        (50.0, 50),
        (100.0, 100),
        (250.0, 200),
        (350.0, 300),
        (430.0, 400),
        (600.0, 500),
    ),
    "no2_ug_m3": (
        (40.0, 50),
        (80.0, 100),
        (180.0, 200),
        (280.0, 300),
        (400.0, 400),
        (600.0, 500),
    ),
    "so2_ug_m3": (
        (40.0, 50),
        (80.0, 100),
        (380.0, 200),
        (800.0, 300),
        (1600.0, 400),
        (2000.0, 500),
    ),
    # CPCB breakpoints are in mg/m³; CO is supplied in µg/m³ and converted.
    "co_ug_m3": (
        (1.0, 50),
        (2.0, 100),
        (10.0, 200),
        (17.0, 300),
        (34.0, 400),
        (50.0, 500),
    ),
    "o3_ug_m3": (
        (50.0, 50),
        (100.0, 100),
        (168.0, 200),
        (208.0, 300),
        (748.0, 400),
        (1000.0, 500),
    ),
}

AVERAGING_HOURS: dict[Pollutant, int] = {
    "pm2_5": 24,
    "pm10": 24,
    "no2_ug_m3": 24,
    "so2_ug_m3": 24,
    "co_ug_m3": 8,
    "o3_ug_m3": 8,
}

_COVERAGE_NAMES: dict[Pollutant, str] = {
    "pm2_5": "pm2_5",
    "pm10": "pm10",
    "no2_ug_m3": "no2",
    "so2_ug_m3": "so2",
    "co_ug_m3": "co",
    "o3_ug_m3": "o3",
}

AQI_CATEGORIES: tuple[str, ...] = (
    "good",
    "satisfactory",
    "moderate",
    "poor",
    "very_poor",
    "severe",
)

_KNOWLEDGE_SOURCE = (
    "CPCB 2014 National AQI method (IES Arthapedia summary of CPCB guidance)"
)


@dataclass(frozen=True)
class AveragingInfo:
    pollutant: Pollutant
    window: str
    hours: int
    valid_hours: int
    required_hours: int
    method: str = "rolling_mean"

    @property
    def complete(self) -> bool:
        return self.valid_hours >= self.required_hours


@dataclass(frozen=True)
class SubIndex:
    pollutant: Pollutant
    concentration: float
    index: float


@dataclass(frozen=True)
class AqiResult:
    value: int
    category: str
    dominant_pollutant: Pollutant
    coverage: tuple[str, ...]
    partial: bool
    basis: str = "computed from CPCB averaging windows"
    averaging: tuple[AveragingInfo, ...] = ()
    method: str = "CPCB-2014"
    source: str = _KNOWLEDGE_SOURCE


@dataclass(frozen=True)
class AqiAssessment:
    aqi: AqiResult | None
    reason: str | None
    averaging: tuple[AveragingInfo, ...]


def category_for(value: int) -> str:
    if value <= 50:
        return AQI_CATEGORIES[0]
    if value <= 100:
        return AQI_CATEGORIES[1]
    if value <= 200:
        return AQI_CATEGORIES[2]
    if value <= 300:
        return AQI_CATEGORIES[3]
    if value <= 400:
        return AQI_CATEGORIES[4]
    return AQI_CATEGORIES[5]


def required_hours(window_hours: int) -> int:
    """CPCB completeness: 16 of 24 hours, or 75% of a shorter window."""
    if window_hours >= 24:
        return 16
    return (window_hours * 3 + 3) // 4


def sub_index(pollutant: Pollutant, concentration: float) -> float:
    """Return the pollutant sub-index, clamped to 0..500.

    The interpolation is linear inside the CPCB band. CO is supplied in µg/m³
    and converted to mg/m³ because the official breakpoints are in mg/m³.
    """
    if concentration < 0:
        raise ValueError("Concentration cannot be negative.")
    value = concentration / 1000.0 if pollutant == "co_ug_m3" else concentration
    previous_boundary = 0.0
    previous_index = 0.0
    for boundary, index_hi in _BREAKPOINTS[pollutant]:
        if value <= boundary:
            if boundary <= previous_boundary:
                return float(index_hi)
            fraction = (value - previous_boundary) / (boundary - previous_boundary)
            return min(
                500.0,
                max(
                    0.0,
                    previous_index + fraction * (index_hi - previous_index),
                ),
            )
        previous_boundary = boundary
        previous_index = float(index_hi)
    return 500.0


def rolling_averages(
    series: Mapping[str, Sequence[float | None]],
    *,
    end: int | None = None,
    basis_hours: int = 1,
) -> dict[Pollutant, tuple[float | None, AveragingInfo]]:
    """Average each pollutant over its CPCB window ending at ``end``.

    ``series`` maps app pollutant keys to hourly values. ``None`` values count
    as missing hours, not zeros. Fewer than the required valid hours yields an
    incomplete :class:`AveragingInfo`; the caller must not publish a sub-index
    from it.

    ``basis_hours`` is the assumed cadence of the series; it must be 1 for
    hourly provider data. It exists so a caller cannot silently pass daily data.
    """
    if basis_hours != 1:
        raise ValueError("CPCB rolling averages require hourly input.")
    result: dict[Pollutant, tuple[float | None, AveragingInfo]] = {}
    for pollutant, window_hours in AVERAGING_HOURS.items():
        raw = list(series.get(pollutant) or ())
        stop = len(raw) - 1 if end is None else min(end, len(raw) - 1)
        start = max(0, stop - window_hours + 1)
        window = raw[start : stop + 1] if stop >= 0 else []
        valid = [
            float(value)
            for value in window
            if value is not None
            and isinstance(value, (int, float))
            and float(value) >= 0
        ]
        value = sum(valid) / len(valid) if valid else None
        info = AveragingInfo(
            pollutant=pollutant,
            window=f"{window_hours}h",
            hours=window_hours,
            valid_hours=len(valid),
            required_hours=required_hours(window_hours),
        )
        # CPCB: when the 8-hour ozone mean exceeds 208 µg/m³, the latest
        # 1-hour value is used instead of the 8-hour mean.
        if (
            pollutant == "o3_ug_m3"
            and value is not None
            and value > 208.0
            and info.complete
            and valid
        ):
            latest = valid[-1]
            value = latest
            info = AveragingInfo(
                pollutant=pollutant,
                window="1h (8h mean > 208)",
                hours=window_hours,
                valid_hours=len(valid),
                required_hours=info.required_hours,
                method="1h_override",
            )
        result[pollutant] = (value, info)
    return result


def evaluate_cpcb_aqi(
    values: Mapping[str, float | None],
    *,
    averaging: Sequence[AveragingInfo] | None = None,
    basis: str = "computed from CPCB averaging windows",
) -> AqiAssessment:
    """Compute the overall AQI and explain why it is unavailable.

    When ``averaging`` is supplied, only pollutants whose window is complete
    are considered. When it is omitted the values are treated as already
    averaged; this is only appropriate for tests and for callers that have
    performed the averaging themselves.
    """
    complete = (
        {item.pollutant: item for item in averaging if item.complete}
        if averaging is not None
        else None
    )
    subindices: list[SubIndex] = []
    for pollutant, concentration in values.items():
        if pollutant not in _BREAKPOINTS or concentration is None:
            continue
        if complete is not None and pollutant not in complete:
            continue
        subindices.append(
            SubIndex(
                pollutant,
                float(concentration),
                sub_index(pollutant, float(concentration)),
            )
        )

    reported = {item.pollutant for item in subindices}
    if not ({"pm2_5", "pm10"} & reported):
        return AqiAssessment(
            aqi=None,
            reason=(
                "CPCB requires a PM2.5 or PM10 sub-index before an overall AQI "
                "can be reported."
            ),
            averaging=tuple(averaging or ()),
        )
    if len(subindices) < 3:
        return AqiAssessment(
            aqi=None,
            reason=(
                "CPCB requires at least three pollutants with complete "
                "averaging windows; fewer are available."
            ),
            averaging=tuple(averaging or ()),
        )

    dominant = max(subindices, key=lambda item: item.index)
    value = min(500, max(0, round(dominant.index)))
    coverage = tuple(
        _COVERAGE_NAMES[item.pollutant]
        for item in sorted(subindices, key=lambda entry: entry.pollutant)
    )
    return AqiAssessment(
        aqi=AqiResult(
            value=value,
            category=category_for(value),
            dominant_pollutant=dominant.pollutant,
            coverage=coverage,
            partial=len(subindices) < len(_BREAKPOINTS),
            basis=basis,
            averaging=tuple(averaging or ()),
        ),
        reason=None,
        averaging=tuple(averaging or ()),
    )


def compute_cpcb_aqi(values: dict[str, float | None]) -> AqiResult | None:
    """Backward-compatible wrapper for already-averaged values.

    New code should call :func:`evaluate_cpcb_aqi` with averaging metadata and
    surface ``reason`` when the result is unavailable.
    """
    return evaluate_cpcb_aqi(values).aqi
