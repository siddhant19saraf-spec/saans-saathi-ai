"""Location search service with a small in-process cache."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.config import Settings
from app.core.exceptions import ProviderUnavailableError
from app.integrations.geocoding.client import GeocodingClient, GeocodingError
from app.schemas.air import CacheMeta, LocationSearchResult, LocationSearchResults
from app.utils.cache import TTLCache
from app.utils.time import utc_now


@dataclass(frozen=True)
class _Entry:
    payload: LocationSearchResults
    fetched_at: datetime
    expires_at: datetime


class LocationSearchService:
    def __init__(
        self,
        *,
        client: GeocodingClient,
        cache: TTLCache[object],
        settings: Settings,
    ) -> None:
        self._client = client
        self._cache = cache
        self._settings = settings

    async def search(
        self,
        *,
        query: str,
        limit: int,
        country_code: str | None,
    ) -> tuple[LocationSearchResults, CacheMeta]:
        cleaned = query.strip()
        key = f"geocode:{cleaned.casefold()}:{(country_code or '').upper()}:{limit}"
        cached = self._cache.get(key)
        if isinstance(cached, _Entry):
            return cached.payload, CacheMeta(hit=True, expires_at=cached.expires_at)
        try:
            places = await self._client.search(
                query=cleaned,
                count=limit,
                country_code=country_code,
            )
        except GeocodingError as exc:
            raise ProviderUnavailableError(
                "Location search is unavailable right now. Try again shortly."
            ) from exc
        payload = LocationSearchResults(
            query=cleaned,
            results=[
                LocationSearchResult(
                    id=place.id,
                    name=place.name,
                    latitude=place.latitude,
                    longitude=place.longitude,
                    country=place.country,
                    country_code=place.country_code,
                    admin1=place.admin1,
                    timezone=place.timezone,
                    population=place.population,
                )
                for place in places
            ],
            attribution=list(self._client.attribution),
        )
        now = utc_now()
        expires_at = now + timedelta(seconds=self._settings.geocoding_cache_ttl_seconds)
        self._cache.set(
            key,
            _Entry(payload=payload, fetched_at=now, expires_at=expires_at),
            min(self._settings.geocoding_cache_ttl_seconds, 3600),
        )
        return payload, CacheMeta(hit=False, expires_at=expires_at)
