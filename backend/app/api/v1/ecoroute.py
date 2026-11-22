"""Eco-route comparison, emissions calculation and saved journeys."""

from __future__ import annotations

from http import HTTPStatus
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    AirServiceDep,
    CurrentProfile,
    RequestIdDep,
    SessionDep,
    public_rate_limit,
    session_rate_limit,
)
from app.schemas.ecoroute import (
    EcoRouteComparison,
    EcoRouteRequest,
    JourneyOut,
    JourneySave,
    ProviderHealth,
)
from app.schemas.envelope import Envelope, envelope
from app.services import ecoroute_service

router = APIRouter(prefix="/ecoroute", tags=["ecoroute"])

_ECO_ERRORS: dict[int | str, dict[str, Any]] = {
    HTTPStatus.UNAUTHORIZED: {"description": "Missing or invalid bearer token."},
    HTTPStatus.UNPROCESSABLE_ENTITY: {
        "description": (
            "Invalid coordinates, modes, passengers, accessibility needs, "
            "or an unsupported combination."
        )
    },
    HTTPStatus.TOO_MANY_REQUESTS: {"description": "Rate limit exceeded."},
}


@router.post(
    "/compare",
    response_model=Envelope[EcoRouteComparison],
    summary="Compare modes by emissions and exposure",
    description=(
        "Straight-line distance with a circuity factor, mode durations, CO2e "
        "from sourced fuel factors, and a relative inhaled-dose index against "
        "walking. Modes without a verified emission factor report null carbon. "
        "PM2.5 is best-effort: if air data is unavailable the exposure index is "
        "null and the comparison still returns. Accessibility needs filter "
        "available modes; max duration excludes slow options."
    ),
    responses={
        422: {"description": "Invalid coordinates, modes or request shape."},
        429: {"description": "Public rate limit exceeded."},
    },
)
async def compare_route(
    payload: EcoRouteRequest,
    air_service: AirServiceDep,
    request_id: RequestIdDep,
    _limit: None = Depends(public_rate_limit("ecoroute")),
) -> Envelope[EcoRouteComparison]:
    comparison = await ecoroute_service.compare(payload, air_service)
    return envelope(comparison, request_id)


@router.get(
    "/calculate-emissions",
    response_model=Envelope[dict[str, Any]],
    summary="Calculate per-passenger emissions for a mode",
    description=(
        "Deterministic emissions calculation using documented factors. "
        "Returns total and per-passenger CO2e with full factor provenance. "
        "Modes without a verified factor are rejected with 422."
    ),
    responses=_ECO_ERRORS,
)
async def calculate_emissions(
    mode: Annotated[str, Query(description="Travel mode.")],
    distance_km: Annotated[float, Query(ge=0, description="Distance in kilometres.")],
    request_id: RequestIdDep,
    passengers: Annotated[
        int, Query(ge=1, le=8, description="Number of passengers.")
    ] = 1,
    _limit: None = Depends(public_rate_limit("ecoroute")),
) -> Envelope[dict[str, Any]]:
    # Validate mode against the literal type values.
    valid_modes = {
        "walk",
        "cycle",
        "two-wheeler",
        "car",
        "bus",
        "train",
        "metro",
        "shared-mobility",
    }
    if mode not in valid_modes:
        from app.core.exceptions import UnprocessableEntityError

        raise UnprocessableEntityError(
            f"Unsupported mode '{mode}'. Supported: {', '.join(sorted(valid_modes))}.",
            code="UNSUPPORTED_MODE",
        )
    result = await ecoroute_service.calculate_emissions(
        mode=mode,  # type: ignore[arg-type]
        distance_km=distance_km,
        passengers=passengers,
    )
    if result is None:
        from app.core.exceptions import UnprocessableEntityError

        raise UnprocessableEntityError(
            f"No verified emission factor for mode '{mode}'.",
            code="FACTOR_NOT_AVAILABLE",
        )
    return envelope(
        {
            "mode": result.mode,
            "distance_km": result.distance_km,
            "passengers": result.passengers,
            "total_kg_co2e": result.total_kg_co2e,
            "per_passenger_kg_co2e": result.per_passenger_kg_co2e,
            "factor_key": result.factor_key,
            "factor_value": result.factor_value,
            "factor_unit": result.factor_unit,
            "factor_version": result.factor_version,
            "factor_source_url": result.factor_source_url,
            "allocation_method": result.allocation_method,
        },
        request_id,
    )


@router.post(
    "/journeys",
    response_model=Envelope[JourneyOut],
    status_code=HTTPStatus.CREATED,
    summary="Save a journey comparison",
    description="Persists a saved eco-route journey for the authenticated household.",
    responses=_ECO_ERRORS,
)
async def save_journey(
    payload: JourneySave,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("ecoroute-write")),
) -> Envelope[JourneyOut]:
    journey = await ecoroute_service.save_journey(session, profile, payload)
    return envelope(journey, request_id)


@router.get(
    "/journeys",
    response_model=Envelope[list[JourneyOut]],
    summary="List saved journeys",
    responses=_ECO_ERRORS,
)
async def list_journeys(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Envelope[list[JourneyOut]]:
    journeys = await ecoroute_service.list_journeys(
        session, profile, limit=limit, offset=offset
    )
    return envelope(journeys, request_id)


@router.get(
    "/providers/health",
    response_model=Envelope[list[ProviderHealth]],
    summary="Report routing provider health",
    responses={
        HTTPStatus.TOO_MANY_REQUESTS: {"description": "Public rate limit exceeded."}
    },
)
async def provider_health(
    request_id: RequestIdDep,
    _limit: None = Depends(public_rate_limit("ecoroute")),
) -> Envelope[list[ProviderHealth]]:
    health = await ecoroute_service.provider_health()
    return envelope(health, request_id)


__all__ = [
    "calculate_emissions",
    "compare_route",
    "list_journeys",
    "provider_health",
    "save_journey",
]
