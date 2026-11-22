"""Open-Meteo geocoding client.

Only place names and coordinates are exchanged. The API returns zero or more
candidate cities; this client never chooses one on the user's behalf.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal

import httpx

FailureKind = Literal["timeout", "http_error", "parse_error", "rate_limited"]


@dataclass(frozen=True)
class GeocodedPlace:
    id: str
    name: str
    latitude: float
    longitude: float
    country: str | None = None
    country_code: str | None = None
    admin1: str | None = None
    timezone: str | None = None
    population: int | None = None


class GeocodingError(Exception):
    def __init__(
        self,
        message: str,
        *,
        kind: FailureKind = "http_error",
        retryable: bool = True,
    ) -> None:
        self.kind = kind
        self.retryable = retryable and kind not in {"parse_error"}
        super().__init__(message)


class GeocodingClient:
    name = "open-meteo-geocoding"
    attribution = ("Open-Meteo Geocoding API", "GeoNames")

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def search(
        self,
        *,
        query: str,
        count: int,
        country_code: str | None = None,
        language: str = "en",
    ) -> tuple[GeocodedPlace, ...]:
        params: dict[str, str | int] = {
            "name": query,
            "count": count,
            "language": language,
            "format": "json",
        }
        if country_code:
            params["countryCode"] = country_code.upper()
        payload = await self._get("/search", params)
        raw = payload.get("results")
        if raw is None:
            return ()
        if not isinstance(raw, list):
            raise GeocodingError(
                "Geocoding response results are malformed.", kind="parse_error"
            )
        places: list[GeocodedPlace] = []
        seen: set[str] = set()
        for item in raw:
            place = _place(item)
            if place is None or place.id in seen:
                continue
            seen.add(place.id)
            places.append(place)
            if len(places) >= count:
                break
        if raw and not places:
            raise GeocodingError(
                "Geocoding response contained no valid coordinates.",
                kind="parse_error",
            )
        return tuple(places)

    async def _get(self, path: str, params: dict[str, str | int]) -> dict[str, Any]:
        try:
            response = await self._client.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise GeocodingError(
                "Geocoding request timed out.", kind="timeout"
            ) from exc
        except httpx.HTTPError as exc:
            raise GeocodingError(
                "Geocoding request failed.", kind="http_error"
            ) from exc
        if response.status_code != 200:
            kind: FailureKind = (
                "rate_limited" if response.status_code == 429 else "http_error"
            )
            raise GeocodingError(
                f"Geocoding returned HTTP {response.status_code}.",
                kind=kind,
                retryable=response.status_code == 429 or response.status_code >= 500,
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise GeocodingError(
                "Geocoding response was not JSON.", kind="parse_error"
            ) from exc
        if not isinstance(payload, dict):
            raise GeocodingError(
                "Geocoding response shape is invalid.", kind="parse_error"
            )
        return payload


def _place(value: object) -> GeocodedPlace | None:
    if not isinstance(value, dict):
        return None
    raw_id = value.get("id")
    if isinstance(raw_id, bool) or not isinstance(raw_id, (int, str)):
        return None
    name = value.get("name")
    lat = _coordinate(value.get("latitude"), 90.0)
    lon = _coordinate(value.get("longitude"), 180.0)
    if not isinstance(name, str) or not name.strip() or lat is None or lon is None:
        return None
    population = value.get("population")
    return GeocodedPlace(
        id=str(raw_id),
        name=name.strip(),
        latitude=lat,
        longitude=lon,
        country=_text(value.get("country")),
        country_code=_text(value.get("country_code")),
        admin1=_text(value.get("admin1")),
        timezone=_text(value.get("timezone")),
        population=(
            int(population)
            if isinstance(population, (int, float))
            and not isinstance(population, bool)
            and population >= 0
            else None
        ),
    )


def _coordinate(value: object, limit: float) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number) or abs(number) > limit:
        return None
    return number


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None
