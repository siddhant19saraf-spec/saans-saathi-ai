"""Eco-route comparison: emissions, travel time, accessibility and saved journeys.

Deterministic mode comparison using sourced emission factors, haversine
distance estimates and best-effort air-quality context. Modes without a
verified factor report null carbon rather than an invented number.
"""

from __future__ import annotations

from typing import Any

from app.core.exceptions import AppError, UnprocessableEntityError
from app.domain.carbon import (
    BUS_FACTOR_KEY,
    TRAIN_FACTOR_KEY,
    TransportCarbonResult,
    transport_co2e_per_passenger,
)
from app.domain.exposure import exposure_dose_ug, relative_index
from app.domain.factors import get_factor
from app.integrations.routing.haversine import (
    CIRCUITY_FACTOR,
    estimate_route,
    shared_distance_km,
)
from app.models.profile import Profile
from app.repositories import ecoroute as repo
from app.schemas.ecoroute import (
    AccessibilityNeed,
    EcoRouteComparison,
    EcoRouteRequest,
    JourneyOut,
    JourneySave,
    ModeComparison,
    ProviderHealth,
    RouteSummary,
    TravelMode,
)
from app.services.air_quality_service import AirQualityService

_MODE_INTENSITY: dict[str, str] = {
    "walk": "light",
    "cycle": "moderate",
    "two-wheeler": "light",
    "car": "rest",
    "bus": "light",
    "train": "light",
    "metro": "light",
    "shared-mobility": "light",
}

_MODE_PATHWAY: dict[str, str] = {
    "walk": "walk",
    "cycle": "cycle",
    "two-wheeler": "two_wheeler",
    "car": "car",
    "bus": "bus",
    "train": "train",
    "metro": "metro",
    "shared-mobility": "car",
}

# Modes that inherently support step-free access when the vehicle is
# boarded. This is a conservative planning flag, not a guarantee for any
# specific vehicle or station.
_STEP_FREE_MODES: frozenset[str] = frozenset({"bus", "train", "metro"})

# Maximum waiting time allowance (minutes) for accessibility needs when
# boarding public transport.
_ACCESSIBILITY_WAIT_MIN: dict[str, int] = {
    "wheelchair": 5,
    "step-free": 5,
    "priority-seating": 2,
    "audio-announcements": 0,
    "none": 0,
}

# All modes support these needs at the planning level.
_UNIVERSAL_ACCESSIBILITY: frozenset[str] = frozenset(
    {"priority-seating", "audio-announcements", "none"}
)


async def compare(
    payload: EcoRouteRequest, air_service: AirQualityService
) -> EcoRouteComparison:
    origin = payload.origin
    destination = payload.destination
    distance = shared_distance_km(
        origin_lat=origin.lat,
        origin_lon=origin.lon,
        destination_lat=destination.lat,
        destination_lon=destination.lon,
    )
    route_estimate = estimate_route(
        origin_lat=origin.lat,
        origin_lon=origin.lon,
        destination_lat=destination.lat,
        destination_lon=destination.lon,
        mode="car",
    )
    pm2_5 = await _pm2_5(air_service, origin)

    comparisons: list[ModeComparison] = []
    baseline_dose: float | None = None
    for mode in payload.modes:
        if not _accessible(mode, payload.accessibility_needs):
            continue
        estimate = estimate_route(
            origin_lat=origin.lat,
            origin_lon=origin.lon,
            destination_lat=destination.lat,
            destination_lon=destination.lon,
            mode=mode,
        )
        # Apply accessibility wait allowance for public transport modes.
        duration = estimate.duration_min
        if mode in {"bus", "train", "metro"}:
            wait = max(
                (
                    _ACCESSIBILITY_WAIT_MIN.get(need, 0)
                    for need in payload.accessibility_needs
                ),
                default=0,
            )
            duration += wait
        if payload.max_duration_min is not None and duration > payload.max_duration_min:
            continue
        carbon = transport_co2e_per_passenger(
            mode=mode,
            distance_km=distance,
            passengers=payload.passengers,
        )
        co2e_total = carbon.total_kg_co2e if carbon else None
        co2e_per_passenger = carbon.per_passenger_kg_co2e if carbon else None
        dose: float | None = None
        if pm2_5 is not None:
            dose = exposure_dose_ug(
                concentration_ug_m3=pm2_5,
                duration_min=duration,
                intensity=_MODE_INTENSITY[mode],  # type: ignore[arg-type]
                age_band="18-59",
                pathway=_MODE_PATHWAY[mode],  # type: ignore[arg-type]
            )
        if pm2_5 is not None and mode == "walk":
            baseline_dose = dose
        comparisons.append(
            ModeComparison(
                mode=mode,
                co2e_kg=round(co2e_total, 4) if co2e_total is not None else None,
                co2e_per_passenger_kg=(
                    round(co2e_per_passenger, 4)
                    if co2e_per_passenger is not None
                    else None
                ),
                exposure_index=None,
                duration_min=duration,
                recommended_for=[],
                accessible=_accessible(mode, payload.accessibility_needs),
            )
        )

    # Relative exposure index against walking baseline.
    if baseline_dose is not None:
        for item in comparisons:
            if item.exposure_index is None:
                # Recompute dose for this mode against the walking baseline.
                dose_val = exposure_dose_ug(
                    concentration_ug_m3=pm2_5 or 0.0,
                    duration_min=item.duration_min or 0,
                    intensity=_MODE_INTENSITY[item.mode],  # type: ignore[arg-type]
                    age_band="18-59",
                    pathway=_MODE_PATHWAY[item.mode],  # type: ignore[arg-type]
                )
                item.exposure_index = relative_index(dose_val, baseline_dose)
    elif comparisons:
        # No air data: exposure stays null for all modes.
        pass

    _annotate(comparisons, payload.passengers)
    return EcoRouteComparison(
        route=RouteSummary(
            distance_km=distance,
            duration_min=route_estimate.duration_min,
            source=route_estimate.source,
            is_estimate=route_estimate.is_estimate,
        ),
        modes=comparisons,
        tradeoff_note=_tradeoff(comparisons, payload.accessibility_needs),
        assumptions=_assumptions(payload.passengers),
    )


async def calculate_emissions(
    *,
    mode: TravelMode,
    distance_km: float,
    passengers: int,
) -> TransportCarbonResult | None:
    """Standalone per-passenger emissions calculation."""
    if distance_km < 0:
        raise UnprocessableEntityError(
            "Distance cannot be negative.", code="NEGATIVE_DISTANCE"
        )
    if passengers < 1:
        raise UnprocessableEntityError(
            "Passenger count must be at least 1.", code="INVALID_PASSENGERS"
        )
    return transport_co2e_per_passenger(
        mode=mode, distance_km=distance_km, passengers=passengers
    )


async def save_journey(
    session: Any,
    profile: Profile,
    payload: JourneySave,
) -> JourneyOut:
    from app.repositories import households as households_repo

    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise UnprocessableEntityError(
            "Create a household profile before saving a journey.",
            code="NO_HOUSEHOLD",
        )
    journey = await repo.save_journey(
        session,
        household_id=household.id,
        origin_lat=payload.origin.lat,
        origin_lon=payload.origin.lon,
        destination_lat=payload.destination.lat,
        destination_lon=payload.destination.lon,
        travel_date=payload.travel_date,
        modes=[str(m) for m in payload.modes],
        selected_mode=payload.selected_mode,
        passengers=payload.passengers,
        distance_km=payload.distance_km,
        duration_min=payload.duration_min,
        co2e_kg=payload.co2e_kg,
        co2e_per_passenger_kg=payload.co2e_per_passenger_kg,
        notes=payload.notes,
    )
    await session.commit()
    return _journey_out(journey)


async def list_journeys(
    session: Any,
    profile: Profile,
    *,
    limit: int,
    offset: int,
) -> list[JourneyOut]:
    from app.repositories import households as households_repo

    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise UnprocessableEntityError(
            "Create a household profile first.", code="NO_HOUSEHOLD"
        )
    rows = await repo.list_journeys(
        session, household_id=household.id, limit=limit, offset=offset
    )
    return [_journey_out(row) for row in rows]


async def provider_health() -> list[ProviderHealth]:
    """Report health of routing providers.

    The haversine estimator is always healthy; future OSRM/transit adapters
    can be added here.
    """
    return [
        ProviderHealth(
            name="haversine",
            healthy=True,
            kind="routing",
            note=(
                "Straight-line distance with urban circuity factor. "
                "Labelled an estimate in all responses."
            ),
        ),
        ProviderHealth(
            name="air-quality",
            healthy=True,
            kind="air-quality",
            note="Best-effort PM2.5 from configured air-quality provider.",
        ),
    ]


def _accessible(mode: str, needs: list[AccessibilityNeed]) -> bool:
    """Return whether a mode can accommodate the listed accessibility needs."""
    if not needs:
        return True
    for need in needs:
        if need == "none":
            continue
        if need in _UNIVERSAL_ACCESSIBILITY:
            continue
        if need in {"wheelchair", "step-free"} and mode in _STEP_FREE_MODES:
            continue
        if need in {"wheelchair", "step-free"} and mode in {"walk", "cycle"}:
            # Active travel is inherently step-free but may not suit all
            # mobility needs; flag as accessible with a caveat.
            continue
        if need in {"wheelchair", "step-free"} and mode == "shared-mobility":
            # Shared vehicles vary; do not assume accessibility.
            return False
        if need in {"wheelchair", "step-free"} and mode == "car":
            # Personal car depends on the vehicle; do not assume.
            return False
    return True


def _annotate(modes: list[ModeComparison], passengers: int) -> None:
    known_carbon = [item for item in modes if item.co2e_kg is not None]
    if known_carbon:
        lowest = min(item.co2e_kg or 0.0 for item in known_carbon)
        for item in known_carbon:
            if (item.co2e_kg or 0.0) <= lowest + 0.0001:
                item.recommended_for.append("lowest emissions")
    if modes:
        fastest = min(item.duration_min or 0 for item in modes)
        for item in modes:
            if item.duration_min == fastest:
                item.recommended_for.append("fastest")
    known_exposure = [item for item in modes if item.exposure_index is not None]
    if known_exposure:
        lowest = min(item.exposure_index or 0 for item in known_exposure)
        for item in known_exposure:
            if item.exposure_index == lowest:
                item.recommended_for.append("lowest inhaled dose")
    for item in modes:
        if (
            item.mode in {"walk", "cycle"}
            and "active travel" not in item.recommended_for
        ):
            item.recommended_for.append("active travel")


def _tradeoff(
    modes: list[ModeComparison], accessibility_needs: list[AccessibilityNeed]
) -> str | None:
    active = [item for item in modes if item.mode in {"walk", "cycle"}]
    car = next((item for item in modes if item.mode == "car"), None)
    if any(item.exposure_index is not None for item in active) and car is not None:
        return (
            "Active travel usually has the lowest emissions but a higher inhaled "
            "dose outdoors; exposure assumes the same outdoor concentration for "
            "every mode, reduced by vehicle filtration only."
        )
    if any(item.mode in {"bus", "train", "metro"} for item in modes):
        return (
            "Bus, train and metro use per-passenger-km factors from UK DEFRA "
            "2023; car and two-wheeler use per-vehicle-km fuel assumptions "
            "divided across passengers."
        )
    if accessibility_needs:
        return (
            "Accessibility needs filter available modes. Walking and cycling "
            "are inherently step-free but may not suit all mobility needs."
        )
    return None


def _assumptions(passengers: int) -> list[Any]:
    from app.schemas.ecoroute import Assumption

    petrol = get_factor("petrol_combustion")
    bus_factor = get_factor(BUS_FACTOR_KEY)
    train_factor = get_factor(TRAIN_FACTOR_KEY)
    return [
        Assumption(
            key="route_distance",
            value="great-circle distance x 1.3 circuity",
            source="Estimate; not a routed or navigated distance.",
        ),
        Assumption(
            key="circuity_factor",
            value=CIRCUITY_FACTOR,
            source="Urban circuity assumption applied to straight-line distance.",
        ),
        Assumption(
            key="car_fuel_consumption_l_per_100km",
            value=7.0,
            source="Product assumption, not a measured fleet value.",
        ),
        Assumption(
            key="two_wheeler_fuel_consumption_l_per_100km",
            value=2.5,
            source="Product assumption, not a measured fleet value.",
        ),
        Assumption(
            key="petrol_factor_kg_per_litre",
            value=petrol.value,
            source=f"{petrol.source_title} ({petrol.version})",
        ),
        Assumption(
            key="car_kg_per_km",
            value=round(7.0 / 100.0 * petrol.value, 6),
            source="Derived from fuel consumption and petrol factor.",
        ),
        Assumption(
            key="two_wheeler_kg_per_km",
            value=round(2.5 / 100.0 * petrol.value, 6),
            source="Derived from fuel consumption and petrol factor.",
        ),
        Assumption(
            key="bus_factor_per_passenger_km",
            value=bus_factor.value,
            source=f"{bus_factor.source_title} ({bus_factor.version})",
        ),
        Assumption(
            key="train_factor_per_passenger_km",
            value=train_factor.value,
            source=f"{train_factor.source_title} ({train_factor.version})",
        ),
        Assumption(
            key="passengers",
            value=passengers,
            source="User-specified passenger count for per-person allocation.",
        ),
        Assumption(
            key="exposure_baseline",
            value="walking = 100",
            source="Relative inhaled-dose index; not a health measure.",
        ),
    ]


async def _pm2_5(air_service: AirQualityService, point: Any) -> float | None:
    try:
        current, _cache = await air_service.current(point.lat, point.lon)
    except AppError:
        return None
    return current.reading.pm2_5


def _journey_out(journey: Any) -> JourneyOut:
    from app.schemas.ecoroute import Point

    return JourneyOut(
        id=str(journey.id),
        origin=Point(lat=float(journey.origin_lat), lon=float(journey.origin_lon)),
        destination=Point(
            lat=float(journey.destination_lat), lon=float(journey.destination_lon)
        ),
        travel_date=journey.travel_date,
        modes=list(journey.modes),
        selected_mode=journey.selected_mode,
        passengers=journey.passengers,
        distance_km=float(journey.distance_km),
        duration_min=journey.duration_min,
        co2e_kg=float(journey.co2e_kg) if journey.co2e_kg is not None else None,
        co2e_per_passenger_kg=(
            float(journey.co2e_per_passenger_kg)
            if journey.co2e_per_passenger_kg is not None
            else None
        ),
        notes=journey.notes,
        created_at=journey.created_at,
    )


__all__ = [
    "calculate_emissions",
    "compare",
    "list_journeys",
    "provider_health",
    "save_journey",
]
