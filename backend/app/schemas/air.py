"""Air-quality response models.

Field names and nullability are pinned to the frontend Zod contracts in
``frontend/src/features/air-quality/schemas.ts``.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AqiCategory = Literal[
    "good",
    "satisfactory",
    "moderate",
    "poor",
    "very_poor",
    "severe",
]

SourceType = Literal[
    "ground_observation",
    "model_forecast",
    "historical_observation",
]


class Coordinates(BaseModel):
    lat: float
    lon: float


class StationInfo(BaseModel):
    id: str
    name: str
    provider: str
    latitude: float
    longitude: float
    distance_km: float | None = None
    timezone: str | None = None
    is_monitor: bool | None = None


class AirLocation(BaseModel):
    requested: Coordinates
    resolved: Coordinates | None = None
    timezone: str | None = None


class AirReading(BaseModel):
    pm2_5: float | None
    pm10: float | None
    co_ug_m3: float | None
    no2_ug_m3: float | None
    so2_ug_m3: float | None
    o3_ug_m3: float | None
    dust_ug_m3: float | None = None


class AveragingBreakdown(BaseModel):
    pollutant: str
    window: str
    hours: int
    valid_hours: int
    required_hours: int
    method: str
    complete: bool


class CpcbAqi(BaseModel):
    value: int = Field(ge=0, le=500)
    category: AqiCategory
    dominant_pollutant: str
    method: Literal["CPCB-2014"] = "CPCB-2014"
    coverage: list[str]
    partial: bool
    basis: str
    averaging: list[AveragingBreakdown] = Field(default_factory=list)
    source: str


class ProviderAqi(BaseModel):
    us: int | None
    european: int | None
    note: str = "Different scales; not comparable to CPCB AQI"


class Provenance(BaseModel):
    provider: str
    kind: str
    source_type: SourceType
    model: str | None = None
    observed_at: datetime | None
    fetched_at: datetime
    age_minutes: int
    freshness: Literal["fresh", "stale"] = "fresh"
    stale: bool
    station: StationInfo | None = None
    attribution: list[str]


class AirCurrent(BaseModel):
    location: AirLocation
    reading: AirReading
    cpcb_aqi: CpcbAqi | None
    aqi_unavailable_reason: str | None = None
    provider_aqi: ProviderAqi | None = None
    provenance: Provenance


class ForecastPoint(BaseModel):
    time: datetime
    pm2_5: float | None = None
    pm10: float | None = None
    no2_ug_m3: float | None = None
    o3_ug_m3: float | None = None
    co_ug_m3: float | None = None
    so2_ug_m3: float | None = None


class AirForecast(BaseModel):
    location: AirLocation | None = None
    hourly: list[ForecastPoint]
    provenance: Provenance | None = None


class HistoryPoint(BaseModel):
    date: date
    pm2_5: float | None = None
    pm10: float | None = None


class AirHistory(BaseModel):
    daily: list[HistoryPoint]
    provenance: Provenance | None = None


class AirStations(BaseModel):
    provider: str
    radius_km: int
    stations: list[StationInfo]
    fetched_at: datetime
    attribution: list[str]


class ProviderHealth(BaseModel):
    name: str
    status: Literal["ok", "degraded", "unavailable", "not_configured"]
    configured: bool
    source_type: SourceType
    supports_forecast: bool
    supports_history: bool
    supports_stations: bool
    circuit_state: str
    attribution: list[str]
    detail: str


class ProviderHealthList(BaseModel):
    providers: list[ProviderHealth]


class LocationSearchResult(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    country: str | None = None
    country_code: str | None = None
    admin1: str | None = None
    timezone: str | None = None
    population: int | None = None


class LocationSearchResults(BaseModel):
    query: str
    results: list[LocationSearchResult]
    attribution: list[str]


class CacheMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hit: bool
    expires_at: datetime | None = None
