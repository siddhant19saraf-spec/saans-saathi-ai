"""Air-quality read endpoints.

Values come from the resolution chain in ``AirQualityService``; when neither a
fresh nor a labelled stale value exists the response is a 503 problem document
rather than a fabricated measurement. ``provider`` selects Open-Meteo (model),
OpenAQ (ground stations) or CPCB (explicitly unavailable).
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BeforeValidator

from app.api.deps import AirServiceDep, RequestIdDep, public_rate_limit
from app.schemas.air import (
    AirCurrent,
    AirForecast,
    AirHistory,
    AirStations,
    CacheMeta,
    ProviderHealth as ProviderHealthSchema,
    ProviderHealthList,
)
from app.schemas.envelope import Envelope, envelope

router = APIRouter(tags=["air-quality"])

ProviderQuery = Annotated[
    str | None,
    Query(
        pattern="^(open-meteo|openaq|cpcb)$",
        description="Data provider. Defaults to the configured primary provider.",
    ),
]

_LATITUDE = Annotated[
    float,
    Query(ge=-90, le=90, description="WGS84 latitude of the requested point."),
]
_LONGITUDE = Annotated[
    float,
    Query(ge=-180, le=180, description="WGS84 longitude of the requested point."),
]

_NOTES: dict[int | str, dict[str, Any]] = {
    HTTPStatus.TOO_MANY_REQUESTS: {"description": "Public rate limit exceeded."},
    HTTPStatus.SERVICE_UNAVAILABLE: {
        "description": (
            "No fresh or stale data is available from this provider. Providers "
            "are never substituted and measurements are never invented."
        )
    },
}


def _cache_headers(response: Response, cache: CacheMeta) -> None:
    response.headers["X-Data-Cache"] = "hit" if cache.hit else "miss"
    if cache.expires_at is not None:
        response.headers["X-Data-Expires-At"] = cache.expires_at.isoformat()


@router.get(
    "/current",
    response_model=Envelope[AirCurrent],
    summary="Current air quality at a point",
    description=(
        "Returns the latest resolved reading with provenance, source type and "
        "staleness. CPCB AQI is returned only when the official averaging "
        "windows are complete; otherwise the response explains why it is absent."
    ),
    responses=_NOTES,
)
async def read_current(
    lat: _LATITUDE,
    lon: _LONGITUDE,
    service: AirServiceDep,
    request_id: RequestIdDep,
    response: Response,
    provider: ProviderQuery = None,
    _limit: None = Depends(public_rate_limit("air")),
) -> Envelope[AirCurrent]:
    payload, cache = await service.current(lat, lon, provider=provider)
    _cache_headers(response, cache)
    return envelope(payload, request_id)


@router.get(
    "/forecast",
    response_model=Envelope[AirForecast],
    summary="Hourly air-quality forecast",
    description=(
        "Returns up to the requested number of hourly points that the provider "
        "actually supplies. Short horizons are not padded. Only model providers "
        "implement this endpoint."
    ),
    responses=_NOTES,
)
async def read_forecast(
    lat: _LATITUDE,
    lon: _LONGITUDE,
    service: AirServiceDep,
    request_id: RequestIdDep,
    response: Response,
    provider: ProviderQuery = None,
    hours: Annotated[
        Literal[24, 48, 72],
        BeforeValidator(int),
        Query(description="Forecast horizon in hours."),
    ] = 24,
    _limit: None = Depends(public_rate_limit("air")),
) -> Envelope[AirForecast]:
    payload, cache = await service.forecast(lat, lon, hours, provider=provider)
    _cache_headers(response, cache)
    return envelope(payload, request_id)


@router.get(
    "/history",
    response_model=Envelope[AirHistory],
    summary="Daily air-quality history",
    description=(
        "Returns provider-reported daily means for the previous days. History "
        "is cached in process for the configured TTL; it is not persisted."
    ),
    responses=_NOTES,
)
async def read_history(
    lat: _LATITUDE,
    lon: _LONGITUDE,
    service: AirServiceDep,
    request_id: RequestIdDep,
    response: Response,
    provider: ProviderQuery = None,
    days: Annotated[int, Query(ge=1, le=31)] = 7,
    _limit: None = Depends(public_rate_limit("air")),
) -> Envelope[AirHistory]:
    payload, cache = await service.history(lat, lon, days, provider=provider)
    _cache_headers(response, cache)
    return envelope(payload, request_id)


@router.get(
    "/stations",
    response_model=Envelope[AirStations],
    summary="Monitoring stations near a point",
    description=(
        "Returns provider-described stations within the radius, including "
        "distance, owner and licence attribution. Empty results are not padded."
    ),
    responses=_NOTES,
)
async def read_stations(
    lat: _LATITUDE,
    lon: _LONGITUDE,
    service: AirServiceDep,
    request_id: RequestIdDep,
    response: Response,
    provider: Annotated[
        str,
        Query(
            pattern="^(open-meteo|openaq|cpcb)$",
            description="Only providers with station listings are supported.",
        ),
    ] = "openaq",
    radius_km: Annotated[int, Query(ge=1, le=25)] = 25,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    _limit: None = Depends(public_rate_limit("air")),
) -> Envelope[AirStations]:
    payload, cache = await service.stations(
        lat,
        lon,
        radius_km=radius_km,
        limit=limit,
        provider=provider,
    )
    _cache_headers(response, cache)
    return envelope(payload, request_id)


@router.get(
    "/providers/health",
    response_model=Envelope[ProviderHealthList],
    summary="Provider configuration and health",
    description=(
        "Reports each provider separately. An unverified CPCB mechanism is "
        "reported as unavailable rather than claimed as working."
    ),
)
async def read_provider_health(
    service: AirServiceDep,
    request_id: RequestIdDep,
) -> Envelope[ProviderHealthList]:
    health = await service.provider_health()
    return envelope(
        ProviderHealthList(
            providers=[
                ProviderHealthSchema(
                    name=item.name,
                    status=item.status,
                    configured=item.configured,
                    source_type=item.source_type,
                    supports_forecast=item.supports_forecast,
                    supports_history=item.supports_history,
                    supports_stations=item.supports_stations,
                    circuit_state=circuit_state,
                    attribution=list(item.attribution),
                    detail=item.detail,
                )
                for item, circuit_state in health
            ]
        ),
        request_id,
    )
