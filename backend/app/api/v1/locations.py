"""Location search endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import LocationServiceDep, RequestIdDep, public_rate_limit
from app.schemas.air import CacheMeta, LocationSearchResults
from app.schemas.envelope import Envelope, envelope

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get(
    "/search",
    response_model=Envelope[LocationSearchResults],
    summary="Search for a city by name",
    description=(
        "Returns zero or more selectable places with coordinates, region, "
        "country and timezone. The API never picks a result automatically."
    ),
)
async def search_locations(
    q: Annotated[
        str,
        Query(
            min_length=2,
            max_length=80,
            description="City or place name.",
        ),
    ],
    service: LocationServiceDep,
    request_id: RequestIdDep,
    response: Response,
    country_code: Annotated[
        str | None,
        Query(
            min_length=2,
            max_length=2,
            pattern=r"^[A-Za-z]{2}$",
            description="Optional ISO 3166-1 alpha-2 country code.",
        ),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
    _limit: None = Depends(public_rate_limit("locations")),
) -> Envelope[LocationSearchResults]:
    payload, cache = await service.search(
        query=q, limit=limit, country_code=country_code
    )
    _cache_headers(response, cache)
    return envelope(payload, request_id)


def _cache_headers(response: Response, cache: CacheMeta) -> None:
    response.headers["X-Data-Cache"] = "hit" if cache.hit else "miss"
    if cache.expires_at is not None:
        response.headers["X-Data-Expires-At"] = cache.expires_at.isoformat()
