"""Indoor PM2.5 mass-balance estimate.

This is a model, not a measurement. Outputs are intervals derived from the
documented parameter ranges so the UI never implies sensor precision.
"""

from __future__ import annotations

from dataclasses import dataclass

PENETRATION_CLOSED = (0.3, 0.8)
PENETRATION_OPEN = (0.7, 0.9)
ACH_CLOSED = (0.3, 1.0)
ACH_OPEN = (3.0, 10.0)
DEPOSITION = (0.2, 0.5)
DEFAULT_ROOM_AREA_M2 = 20.0
DEFAULT_CEILING_M = 2.7


@dataclass(frozen=True)
class IndoorEstimate:
    pm2_5_low: float
    pm2_5_high: float
    outdoor_pm2_5: float
    volume_m3: float
    purifier_cadr: int


def room_volume_m3(
    *,
    area_m2: float | None = None,
    ceiling_m: float | None = None,
) -> float:
    area = area_m2 if area_m2 is not None else DEFAULT_ROOM_AREA_M2
    ceiling = ceiling_m if ceiling_m is not None else DEFAULT_CEILING_M
    if area <= 0 or ceiling <= 0:
        raise ValueError("Room dimensions must be positive.")
    return area * ceiling


def _concentration(
    *,
    outdoor: float,
    penetration: float,
    ach: float,
    deposition: float,
    cadr: float,
    volume: float,
    indoor_source_ug_per_h: float,
) -> float:
    numerator = penetration * ach * outdoor + indoor_source_ug_per_h / volume
    denominator = ach + deposition + cadr / volume
    return max(0.0, numerator / denominator)


def estimate_indoor_pm25(
    *,
    outdoor_pm2_5: float,
    volume_m3: float,
    purifier_cadr: int = 0,
    windows_open: bool = False,
    indoor_source_ug_per_h: float = 0.0,
    penetration: tuple[float, float] | None = None,
    ach: tuple[float, float] | None = None,
    deposition: tuple[float, float] = DEPOSITION,
) -> IndoorEstimate:
    if outdoor_pm2_5 < 0:
        raise ValueError("Outdoor concentration cannot be negative.")
    penetration_range = penetration or (
        PENETRATION_OPEN if windows_open else PENETRATION_CLOSED
    )
    ach_range = ach or (ACH_OPEN if windows_open else ACH_CLOSED)
    cadr = max(0, purifier_cadr)

    # The mass-balance response to each parameter is monotonic, but the
    # direction differs with a large purifier, so evaluate the corner cases and
    # take the true extremes rather than assuming which corner is lowest.
    estimates = [
        _concentration(
            outdoor=outdoor_pm2_5,
            penetration=penetration,
            ach=ach,
            deposition=dep,
            cadr=cadr,
            volume=volume_m3,
            indoor_source_ug_per_h=indoor_source_ug_per_h,
        )
        for penetration in penetration_range
        for ach in ach_range
        for dep in deposition
    ]
    return IndoorEstimate(
        pm2_5_low=round(min(estimates), 1),
        pm2_5_high=round(max(estimates), 1),
        outdoor_pm2_5=round(outdoor_pm2_5, 1),
        volume_m3=round(volume_m3, 1),
        purifier_cadr=cadr,
    )


def recommended_cadr(volume_m3: float, target_ach: float = 5.0) -> int:
    """Clean-air delivery rate for roughly ``target_ach`` air changes per hour."""
    if volume_m3 <= 0:
        raise ValueError("Volume must be positive.")
    return int(round(volume_m3 * target_ach / 10.0) * 10)
