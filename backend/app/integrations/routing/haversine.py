"""Straight-line route estimates with an explicit urban circuity factor.

No navigation instructions are produced; the result is labelled an estimate in
every API response.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.domain.exposure import Pathway

CIRCUITY_FACTOR = 1.3
EARTH_RADIUS_KM = 6371.0088

MODE_SPEEDS_KMH: dict[str, float] = {
    "walk": 4.8,
    "cycle": 15.0,
    "two-wheeler": 28.0,
    "car": 26.0,
    "bus": 18.0,
    "metro": 32.0,
}

MODE_FIXED_WAIT_MIN: dict[str, float] = {
    "walk": 0.0,
    "cycle": 0.0,
    "two-wheeler": 3.0,
    "car": 5.0,
    "bus": 8.0,
    "metro": 6.0,
}

MODE_PATHWAYS: dict[str, Pathway] = {
    "walk": "walk",
    "cycle": "cycle",
    "two-wheeler": "two_wheeler",
    "car": "car",
    "bus": "bus",
    "metro": "metro",
}


@dataclass(frozen=True)
class RouteEstimate:
    distance_km: float
    duration_min: int
    source: str
    is_estimate: bool


def haversine_km(
    origin_lat: float,
    origin_lon: float,
    destination_lat: float,
    destination_lon: float,
) -> float:
    lat1, lon1, lat2, lon2 = map(
        math.radians, (origin_lat, origin_lon, destination_lat, destination_lon)
    )
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def estimate_route(
    *,
    origin_lat: float,
    origin_lon: float,
    destination_lat: float,
    destination_lon: float,
    mode: str,
) -> RouteEstimate:
    """Estimate distance and travel time for a mode.

    Distance is identical across modes at this abstraction level; only speed
    and fixed waiting differ. A future OSRM adapter can replace this without
    changing callers.
    """
    direct = haversine_km(origin_lat, origin_lon, destination_lat, destination_lon)
    distance = max(0.0, direct * CIRCUITY_FACTOR)
    speed = MODE_SPEEDS_KMH.get(mode, MODE_SPEEDS_KMH["car"])
    wait = MODE_FIXED_WAIT_MIN.get(mode, 0.0)
    travel_min = distance / speed * 60 if speed else 0.0
    duration = max(1, round(travel_min + wait))
    return RouteEstimate(
        distance_km=round(distance, 2),
        duration_min=duration,
        source="haversine",
        is_estimate=True,
    )


def shared_distance_km(
    *,
    origin_lat: float,
    origin_lon: float,
    destination_lat: float,
    destination_lon: float,
) -> float:
    return round(
        haversine_km(origin_lat, origin_lon, destination_lat, destination_lon)
        * CIRCUITY_FACTOR,
        2,
    )
