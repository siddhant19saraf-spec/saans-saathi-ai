"""Air-quality resolution chain.

Order: in-process cache -> PostgreSQL snapshot -> live provider -> labelled
stale row -> 503. A provider failure never produces invented measurements.

Each provider has its own circuit breaker, daily call budget and cache keys.
Open-Meteo is model output, OpenAQ is ground observations and CPCB is an
explicit unavailable provider; their responses are never merged.
"""

from __future__ import annotations

import asyncio
import secrets
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any, TypeVar, cast

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import (
    BadRequestError,
    DatabaseUnavailableError,
    ProviderUnavailableError,
)
from app.core.logging import get_logger
from app.domain.aqi import AqiResult, AveragingInfo, evaluate_cpcb_aqi
from app.integrations.air_quality.base import (
    AirQualityProvider,
    AirQualityProviderError,
    AirQualityStationProvider,
    AveragingDetail,
    ProviderForecast,
    ProviderHealth,
    ProviderHistory,
    ProviderReading,
    SourceType,
    StationInfo,
)
from app.integrations.air_quality.circuit import CircuitBreaker
from app.models.air import AirQualityForecast, AirQualitySnapshot
from app.repositories import air as air_repo
from app.schemas.air import (
    AirCurrent,
    AirForecast,
    AirHistory,
    AirLocation,
    AirReading,
    AirStations,
    AveragingBreakdown,
    CacheMeta,
    Coordinates,
    CpcbAqi,
    ForecastPoint,
    HistoryPoint,
    Provenance,
    ProviderAqi,
    StationInfo as StationSchema,
)
from app.utils.cache import TTLCache
from app.utils.time import utc_now

logger = get_logger(__name__)

_MEMORY_TTL_SECONDS = 60
_STATIONS_TTL_SECONDS = 300
_MAX_ATTEMPTS = 3
_BACKOFF_BASE_SECONDS = 0.2
_POLLUTANT_KEYS = (
    "pm2_5",
    "pm10",
    "co_ug_m3",
    "no2_ug_m3",
    "so2_ug_m3",
    "o3_ug_m3",
)

T = TypeVar("T")


@dataclass(frozen=True)
class ProviderBinding:
    provider: AirQualityProvider
    breaker: CircuitBreaker
    budget_key: str
    budget: int


@dataclass(frozen=True)
class _CurrentEntry:
    payload: AirCurrent
    fetched_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class _ForecastEntry:
    payload: AirForecast
    fetched_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class _HistoryEntry:
    payload: AirHistory
    fetched_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class _StationsEntry:
    payload: AirStations
    fetched_at: datetime
    expires_at: datetime


class AirQualityService:
    def __init__(
        self,
        *,
        settings: Settings,
        provider: AirQualityProvider,
        breaker: CircuitBreaker,
        cache: TTLCache[object],
        session: AsyncSession | None,
        bindings: Mapping[str, ProviderBinding] | None = None,
    ) -> None:
        self._settings = settings
        self._provider = provider
        self._default = ProviderBinding(
            provider=provider,
            breaker=breaker,
            budget_key="openaq" if provider.name == "openaq" else "openmeteo",
            budget=(
                settings.openaq_daily_call_budget
                if provider.name == "openaq"
                else settings.openmeteo_daily_call_budget
            ),
        )
        self._bindings: dict[str, ProviderBinding] = dict(bindings or {})
        self._bindings.setdefault(provider.name, self._default)
        self._cache = cache
        self._session = session

    # -- public reads -----------------------------------------------------

    async def current(
        self,
        lat: float,
        lon: float,
        *,
        provider: str | None = None,
    ) -> tuple[AirCurrent, CacheMeta]:
        binding = self._select(provider)
        lat_key, lon_key = _keys(lat, lon)
        cache_key = f"current:{binding.provider.name}:{lat_key}:{lon_key}"
        cached = self._cache.get(cache_key)
        if isinstance(cached, _CurrentEntry):
            return cached.payload, CacheMeta(hit=True, expires_at=cached.expires_at)

        snapshot = await self._read_snapshot(binding, lat_key, lon_key, stale=False)
        if snapshot is not None:
            payload = _current_from_snapshot(snapshot, stale=False)
            self._cache.set(
                cache_key,
                _CurrentEntry(
                    payload=payload,
                    fetched_at=snapshot.fetched_at,
                    expires_at=snapshot.expires_at,
                ),
                _MEMORY_TTL_SECONDS,
            )
            return payload, CacheMeta(hit=False, expires_at=snapshot.expires_at)

        reading = await self._fetch_current(binding, float(lat_key), float(lon_key))
        if reading is not None:
            now = utc_now()
            expires_at = now + timedelta(seconds=self._settings.air_current_ttl_seconds)
            payload = _current_from_reading(reading, lat, lon, fetched_at=now)
            self._cache.set(
                cache_key,
                _CurrentEntry(payload=payload, fetched_at=now, expires_at=expires_at),
                _MEMORY_TTL_SECONDS,
            )
            await self._store_snapshot(reading, lat_key, lon_key, now, expires_at)
            return payload, CacheMeta(hit=False, expires_at=expires_at)

        stale = await self._read_snapshot(binding, lat_key, lon_key, stale=True)
        if stale is not None:
            return _current_from_snapshot(stale, stale=True), CacheMeta(
                hit=False, expires_at=stale.expires_at
            )
        raise ProviderUnavailableError(
            _unavailable_message(binding.provider.name, "Air-quality data")
        )

    async def forecast(
        self,
        lat: float,
        lon: float,
        hours: int,
        *,
        provider: str | None = None,
    ) -> tuple[AirForecast, CacheMeta]:
        binding = self._select(provider)
        _require(binding.provider, "forecast", "Forecast")
        lat_key, lon_key = _keys(lat, lon)
        cache_key = f"forecast:{binding.provider.name}:{lat_key}:{lon_key}:{hours}"
        cached = self._cache.get(cache_key)
        if isinstance(cached, _ForecastEntry):
            return cached.payload, CacheMeta(hit=True, expires_at=cached.expires_at)

        row = await self._read_forecast(binding, lat_key, lon_key, stale=False)
        if row is not None:
            payload = _forecast_from_series(
                row.series,
                requested=_coordinates(lat, lon),
                hours=hours,
                stale=False,
                default_provider=binding.provider.name,
            )
            if payload is not None:
                self._cache.set(
                    cache_key,
                    _ForecastEntry(
                        payload=payload,
                        fetched_at=row.issued_at,
                        expires_at=row.expires_at,
                    ),
                    _MEMORY_TTL_SECONDS,
                )
                return payload, CacheMeta(hit=False, expires_at=row.expires_at)

        forecast = await self._fetch_forecast(
            binding, float(lat_key), float(lon_key), hours
        )
        if forecast is not None:
            now = utc_now()
            expires_at = now + timedelta(
                seconds=self._settings.air_forecast_ttl_seconds
            )
            payload = _forecast_from_provider(
                forecast, requested=_coordinates(lat, lon), hours=hours
            )
            self._cache.set(
                cache_key,
                _ForecastEntry(payload=payload, fetched_at=now, expires_at=expires_at),
                _MEMORY_TTL_SECONDS,
            )
            await self._store_forecast(forecast, lat_key, lon_key, expires_at)
            return payload, CacheMeta(hit=False, expires_at=expires_at)

        stale = await self._read_forecast(binding, lat_key, lon_key, stale=True)
        if stale is not None:
            payload = _forecast_from_series(
                stale.series,
                requested=_coordinates(lat, lon),
                hours=hours,
                stale=True,
                default_provider=binding.provider.name,
            )
            if payload is not None:
                return payload, CacheMeta(hit=False, expires_at=stale.expires_at)
        raise ProviderUnavailableError(
            _unavailable_message(binding.provider.name, "Forecast data")
        )

    async def history(
        self,
        lat: float,
        lon: float,
        days: int,
        *,
        provider: str | None = None,
    ) -> tuple[AirHistory, CacheMeta]:
        binding = self._select(provider)
        _require(binding.provider, "history", "Historical air-quality data")
        lat_key, lon_key = _keys(lat, lon)
        cache_key = f"history:{binding.provider.name}:{lat_key}:{lon_key}:{days}"
        cached = self._cache.get(cache_key)
        if isinstance(cached, _HistoryEntry):
            return cached.payload, CacheMeta(hit=True, expires_at=cached.expires_at)

        history = await self._fetch_history(
            binding, float(lat_key), float(lon_key), days
        )
        if history is None:
            raise ProviderUnavailableError(
                _unavailable_message(
                    binding.provider.name, "Historical air-quality data"
                )
            )
        now = utc_now()
        expires_at = now + timedelta(seconds=self._settings.air_history_ttl_seconds)
        payload = AirHistory(
            daily=[
                HistoryPoint(
                    date=date.fromisoformat(day.date),
                    pm2_5=day.pm2_5,
                    pm10=day.pm10,
                )
                for day in history.days
            ],
            provenance=Provenance(
                provider=history.provider,
                kind="modelled",
                source_type=_source_type(history.source_type, "model_forecast"),
                model=history.model,
                observed_at=None,
                fetched_at=history.issued_at,
                age_minutes=_age_minutes(history.issued_at),
                stale=False,
                attribution=list(history.attribution),
            ),
        )
        self._cache.set(
            cache_key,
            _HistoryEntry(payload=payload, fetched_at=now, expires_at=expires_at),
            _MEMORY_TTL_SECONDS,
        )
        return payload, CacheMeta(hit=False, expires_at=expires_at)

    async def stations(
        self,
        lat: float,
        lon: float,
        *,
        radius_km: int,
        limit: int,
        provider: str = "openaq",
    ) -> tuple[AirStations, CacheMeta]:
        binding = self._select(provider)
        if not getattr(binding.provider, "supports_stations", False):
            raise ProviderUnavailableError(
                f"{binding.provider.name} does not expose station listings."
            )
        lat_key, lon_key = _keys(lat, lon)
        cache_key = (
            f"stations:{binding.provider.name}:{lat_key}:{lon_key}:"
            f"{radius_km}:{limit}"
        )
        cached = self._cache.get(cache_key)
        if isinstance(cached, _StationsEntry):
            return cached.payload, CacheMeta(hit=True, expires_at=cached.expires_at)

        provider_with_stations = cast(AirQualityStationProvider, binding.provider)
        result = await self._call(
            binding,
            lambda: provider_with_stations.stations(
                lat, lon, radius_km=radius_km, limit=limit
            ),
            lat=lat,
            lon=lon,
        )
        if result is None:
            raise ProviderUnavailableError(
                _unavailable_message(binding.provider.name, "Station data")
            )
        stations, attribution = result
        now = utc_now()
        expires_at = now + timedelta(seconds=_STATIONS_TTL_SECONDS)
        payload = AirStations(
            provider=binding.provider.name,
            radius_km=radius_km,
            stations=[_station_schema(station) for station in stations],
            fetched_at=now,
            attribution=list(attribution),
        )
        self._cache.set(
            cache_key,
            _StationsEntry(payload=payload, fetched_at=now, expires_at=expires_at),
            _STATIONS_TTL_SECONDS,
        )
        return payload, CacheMeta(hit=False, expires_at=expires_at)

    async def provider_health(self) -> list[tuple[ProviderHealth, str]]:
        results: list[tuple[ProviderHealth, str]] = []
        for binding in self._bindings.values():
            circuit_state = binding.breaker.state
            health_method = getattr(binding.provider, "health", None)
            if callable(health_method):
                try:
                    health = await health_method()
                except Exception:  # health must never take the endpoint down
                    logger.warning(
                        "air_provider_health_failed",
                        provider=binding.provider.name,
                    )
                    health = _fallback_health(binding.provider)
            else:
                health = _fallback_health(binding.provider)
            if circuit_state == "open":
                health = replace(health, status="degraded")
            results.append((health, circuit_state))
        return results

    # -- provider selection ----------------------------------------------

    def _select(self, provider: str | None) -> ProviderBinding:
        if provider is None or provider == self._provider.name:
            return self._default
        binding = self._bindings.get(provider)
        if binding is None:
            raise BadRequestError("Unknown air-quality provider.")
        return binding

    # -- provider calls ---------------------------------------------------

    async def _fetch_current(
        self, binding: ProviderBinding, lat: float, lon: float
    ) -> ProviderReading | None:
        if not await self._live_allowed(binding):
            return None
        return await self._call(
            binding, lambda: binding.provider.current(lat, lon), lat=lat, lon=lon
        )

    async def _fetch_forecast(
        self, binding: ProviderBinding, lat: float, lon: float, hours: int
    ) -> ProviderForecast | None:
        if not await self._live_allowed(binding):
            return None
        return await self._call(
            binding,
            lambda: binding.provider.forecast(lat, lon, hours),
            lat=lat,
            lon=lon,
        )

    async def _fetch_history(
        self, binding: ProviderBinding, lat: float, lon: float, days: int
    ) -> ProviderHistory | None:
        if not await self._live_allowed(binding):
            return None
        return await self._call(
            binding,
            lambda: binding.provider.history(lat, lon, days),
            lat=lat,
            lon=lon,
        )

    async def _call(
        self,
        binding: ProviderBinding,
        call: Callable[[], Awaitable[T]],
        *,
        lat: float,
        lon: float,
    ) -> T | None:
        if not binding.breaker.allow():
            logger.info(
                "air_provider_circuit_open_skip", provider=binding.provider.name
            )
            return None
        last_error: AirQualityProviderError | None = None
        started = time.perf_counter()
        lat_key, lon_key = _keys(lat, lon)
        for attempt in range(_MAX_ATTEMPTS):
            try:
                result = await call()
            except AirQualityProviderError as exc:
                last_error = exc
                if exc.kind in {
                    "timeout",
                    "http_error",
                    "parse_error",
                    "rate_limited",
                }:
                    binding.breaker.record_failure(timeout=exc.kind == "timeout")
                logger.warning(
                    "air_provider_failure",
                    provider=binding.provider.name,
                    kind=exc.kind,
                    attempt=attempt + 1,
                )
                if not exc.retryable or attempt + 1 >= _MAX_ATTEMPTS:
                    break
                delay = exc.retry_after
                if delay is None:
                    delay = _BACKOFF_BASE_SECONDS * (2**attempt)
                    delay += secrets.randbelow(1000) / 1000 * _BACKOFF_BASE_SECONDS
                await asyncio.sleep(min(2.0, max(0.0, delay)))
                continue
            binding.breaker.record_success()
            await self._log_fetch(
                binding,
                "ok",
                latency_ms=round((time.perf_counter() - started) * 1000),
                lat_key=lat_key,
                lon_key=lon_key,
            )
            return result
        await self._log_fetch(
            binding,
            last_error.kind if last_error is not None else "circuit_open",
            http_status=last_error.http_status if last_error is not None else None,
            latency_ms=round((time.perf_counter() - started) * 1000),
            lat_key=lat_key,
            lon_key=lon_key,
        )
        return None

    async def _live_allowed(self, binding: ProviderBinding) -> bool:
        if self._session is None:
            return True
        try:
            allowed = await air_repo.consume_budget(
                self._session,
                key=binding.budget_key,
                budget=binding.budget,
                day=utc_now().date(),
            )
            # Commit before the upstream call so a concurrent request sees the
            # increment and the row lock is released.
            await self._session.commit()
            return allowed
        except SQLAlchemyError:
            await self._session.rollback()
            logger.warning("air_budget_check_failed", provider=binding.provider.name)
            return False

    async def _log_fetch(
        self,
        binding: ProviderBinding,
        status: str,
        *,
        latency_ms: int,
        lat_key: Decimal,
        lon_key: Decimal,
        http_status: int | None = None,
    ) -> None:
        if self._session is None:
            return
        safe_status = (
            status
            if status
            in {
                "ok",
                "timeout",
                "http_error",
                "parse_error",
                "circuit_open",
                "rate_limited",
                "unauthorized",
                "not_configured",
                "not_found",
                "unsupported",
            }
            else "http_error"
        )
        try:
            await air_repo.log_fetch(
                self._session,
                provider=binding.provider.name,
                status=safe_status,
                http_status=http_status,
                latency_ms=latency_ms,
                lat_key=lat_key,
                lon_key=lon_key,
            )
            await self._session.commit()
        except SQLAlchemyError:
            await self._session.rollback()

    # -- persistence ------------------------------------------------------

    async def _read_snapshot(
        self,
        binding: ProviderBinding,
        lat_key: Decimal,
        lon_key: Decimal,
        *,
        stale: bool,
    ) -> AirQualitySnapshot | None:
        if self._session is None:
            return None
        max_age = (
            self._settings.air_stale_max_age_seconds
            if stale
            else self._settings.air_current_ttl_seconds
        )
        try:
            return await air_repo.latest_snapshot(
                self._session,
                provider=binding.provider.name,
                lat_key=lat_key,
                lon_key=lon_key,
                max_age=timedelta(seconds=max_age),
            )
        except SQLAlchemyError as exc:
            await self._session.rollback()
            if stale:
                return None
            raise DatabaseUnavailableError() from exc

    async def _read_forecast(
        self,
        binding: ProviderBinding,
        lat_key: Decimal,
        lon_key: Decimal,
        *,
        stale: bool,
    ) -> AirQualityForecast | None:
        if self._session is None:
            return None
        max_age = (
            self._settings.air_stale_max_age_seconds
            if stale
            else self._settings.air_forecast_ttl_seconds
        )
        try:
            return await air_repo.latest_forecast(
                self._session,
                provider=binding.provider.name,
                lat_key=lat_key,
                lon_key=lon_key,
                max_age=timedelta(seconds=max_age),
            )
        except SQLAlchemyError as exc:
            await self._session.rollback()
            if stale:
                return None
            raise DatabaseUnavailableError() from exc

    async def _store_snapshot(
        self,
        reading: ProviderReading,
        lat_key: Decimal,
        lon_key: Decimal,
        fetched_at: datetime,
        expires_at: datetime,
    ) -> None:
        if self._session is None:
            return
        try:
            await air_repo.upsert_snapshot(
                self._session,
                provider=reading.provider,
                lat_key=lat_key,
                lon_key=lon_key,
                kind=reading.kind,
                source_type=_source_type(reading.source_type, reading.kind),
                observed_at=reading.observed_at,
                fetched_at=fetched_at,
                expires_at=expires_at,
                values=reading.values,
                us_aqi=reading.us_aqi,
                eu_aqi=reading.european_aqi,
                station_name=reading.station.name if reading.station else None,
                raw=_snapshot_raw(reading),
            )
            await self._session.commit()
        except SQLAlchemyError:
            await self._session.rollback()

    async def _store_forecast(
        self,
        forecast: ProviderForecast,
        lat_key: Decimal,
        lon_key: Decimal,
        expires_at: datetime,
    ) -> None:
        if self._session is None:
            return
        try:
            await air_repo.upsert_forecast(
                self._session,
                provider=forecast.provider,
                lat_key=lat_key,
                lon_key=lon_key,
                issued_at=forecast.issued_at,
                series=_series_payload(forecast),
                expires_at=expires_at,
            )
            await self._session.commit()
        except SQLAlchemyError:
            await self._session.rollback()


# -- pure mapping helpers -------------------------------------------------


def _keys(lat: float, lon: float) -> tuple[Decimal, Decimal]:
    return air_repo.key_for(lat), air_repo.key_for(lon)


def _coordinates(lat: float, lon: float) -> AirLocation:
    return AirLocation(requested=Coordinates(lat=lat, lon=lon))


def _age_minutes(value: datetime) -> int:
    delta = utc_now() - value.astimezone(UTC)
    return max(0, int(delta.total_seconds() // 60))


def _source_type(value: str | None, kind: str) -> SourceType:
    if value in {
        "ground_observation",
        "model_forecast",
        "historical_observation",
    }:
        return cast(SourceType, value)
    return "ground_observation" if kind == "measured" else "model_forecast"


def _require(provider: AirQualityProvider, capability: str, label: str) -> None:
    if not getattr(provider, f"supports_{capability}", True):
        raise ProviderUnavailableError(
            f"{provider.name} does not provide {label.lower()}."
        )


def _unavailable_message(provider: str, label: str) -> str:
    if provider == "openaq":
        return (
            f"{label} is unavailable for this point. OpenAQ coverage is "
            "incomplete and no nearby station returned usable data."
        )
    if provider == "cpcb":
        return (
            f"{label} from CPCB is unavailable: the official data access "
            "mechanism could not be verified, so no station values are reported."
        )
    return f"{label} is unavailable right now. Try again shortly."


def _station_schema(station: StationInfo) -> StationSchema:
    return StationSchema(
        id=station.id,
        name=station.name,
        provider=station.provider,
        latitude=station.latitude,
        longitude=station.longitude,
        distance_km=station.distance_km,
        timezone=station.timezone,
        is_monitor=station.is_monitor,
    )


def _aqi_from_windows(
    averages: Mapping[str, float | None],
    windows: Mapping[str, AveragingDetail],
    *,
    source_type: SourceType,
) -> tuple[CpcbAqi | None, str | None]:
    if not windows:
        return (
            None,
            "CPCB averaging windows are not available for this reading, so an "
            "overall AQI is not reported.",
        )
    details = tuple(
        AveragingInfo(
            pollutant=cast(Any, pollutant),
            window=detail.window,
            hours=detail.hours,
            valid_hours=detail.valid_hours,
            required_hours=detail.required_hours,
            method=detail.method,
        )
        for pollutant, detail in windows.items()
    )
    basis = (
        "CPCB 2014 method applied to modelled hourly series; this is not a "
        "monitoring-station measurement."
        if source_type == "model_forecast"
        else "CPCB 2014 method applied to station hourly series."
    )
    assessment = evaluate_cpcb_aqi(averages, averaging=details, basis=basis)
    if assessment.aqi is None:
        return None, assessment.reason
    return _cpcb_schema(assessment.aqi, windows), None


def _cpcb_schema(result: AqiResult, windows: Mapping[str, AveragingDetail]) -> CpcbAqi:
    return CpcbAqi(
        value=result.value,
        category=cast(Any, result.category),
        dominant_pollutant=result.dominant_pollutant,
        coverage=list(result.coverage),
        partial=result.partial,
        basis=result.basis,
        averaging=[
            AveragingBreakdown(
                pollutant=pollutant,
                window=detail.window,
                hours=detail.hours,
                valid_hours=detail.valid_hours,
                required_hours=detail.required_hours,
                method=detail.method,
                complete=detail.complete,
            )
            for pollutant, detail in windows.items()
        ],
        source=result.source,
    )


def _provided_aqi(us: int | None, european: int | None) -> ProviderAqi | None:
    if us is None and european is None:
        return None
    return ProviderAqi(us=us, european=european)


def _reading(values: dict[str, float | None], dust: float | None = None) -> AirReading:
    return AirReading(
        pm2_5=values.get("pm2_5"),
        pm10=values.get("pm10"),
        co_ug_m3=values.get("co_ug_m3"),
        no2_ug_m3=values.get("no2_ug_m3"),
        so2_ug_m3=values.get("so2_ug_m3"),
        o3_ug_m3=values.get("o3_ug_m3"),
        dust_ug_m3=dust,
    )


def _current_from_reading(
    reading: ProviderReading, lat: float, lon: float, *, fetched_at: datetime
) -> AirCurrent:
    values = {key: reading.values.get(key) for key in _POLLUTANT_KEYS}
    source_type = _source_type(reading.source_type, reading.kind)
    cpcb, reason = _aqi_from_windows(
        reading.averages, reading.average_windows, source_type=source_type
    )
    station = _station_schema(reading.station) if reading.station else None
    stale = "stale_measurement" in reading.quality_flags
    return AirCurrent(
        location=AirLocation(
            requested=Coordinates(lat=lat, lon=lon),
            resolved=(
                Coordinates(lat=reading.latitude, lon=reading.longitude)
                if reading.latitude is not None and reading.longitude is not None
                else None
            ),
            timezone=reading.timezone,
        ),
        reading=_reading(values, reading.values.get("dust_ug_m3")),
        cpcb_aqi=cpcb,
        aqi_unavailable_reason=reason,
        provider_aqi=_provided_aqi(reading.us_aqi, reading.european_aqi),
        provenance=Provenance(
            provider=reading.provider,
            kind=reading.kind,
            source_type=source_type,
            model=reading.model,
            observed_at=reading.observed_at,
            fetched_at=fetched_at,
            age_minutes=_age_minutes(reading.observed_at),
            freshness="stale" if stale else "fresh",
            stale=stale,
            station=station,
            attribution=list(reading.attribution),
        ),
    )


def _current_from_snapshot(snapshot: AirQualitySnapshot, *, stale: bool) -> AirCurrent:
    values = {key: getattr(snapshot, key) for key in _POLLUTANT_KEYS}
    raw = snapshot.raw if isinstance(snapshot.raw, dict) else {}
    raw_aqi = raw.get("aqi")
    envelope: dict[str, Any] = raw_aqi if isinstance(raw_aqi, dict) else {}
    raw_averages = envelope.get("averages")
    averages = (
        {key: value for key, value in raw_averages.items() if isinstance(key, str)}
        if isinstance(raw_averages, dict)
        else {}
    )
    windows = _windows_from_raw(envelope.get("windows"))
    source_type = _source_type(
        raw.get("source_type") if isinstance(raw.get("source_type"), str) else None,
        snapshot.kind,
    )
    cpcb, reason = _aqi_from_windows(averages, windows, source_type=source_type)
    if not windows:
        reason = (
            "Averaging windows were not stored for this cached row, so an "
            "overall AQI is not reported."
        )
    flags = raw.get("quality_flags")
    stale_measurement = isinstance(flags, list) and "stale_measurement" in flags
    attribution = raw.get("attribution")
    station_raw = raw.get("station")
    return AirCurrent(
        location=AirLocation(
            requested=Coordinates(
                lat=float(snapshot.lat_key), lon=float(snapshot.lon_key)
            ),
            resolved=None,
            timezone=(
                raw.get("timezone") if isinstance(raw.get("timezone"), str) else None
            ),
        ),
        reading=_reading(values, snapshot.dust_ug_m3),
        cpcb_aqi=cpcb,
        aqi_unavailable_reason=reason,
        provider_aqi=_provided_aqi(snapshot.us_aqi, snapshot.eu_aqi),
        provenance=Provenance(
            provider=snapshot.provider,
            kind=snapshot.kind,
            source_type=source_type,
            model=raw.get("model") if isinstance(raw.get("model"), str) else None,
            observed_at=snapshot.observed_at,
            fetched_at=snapshot.fetched_at,
            age_minutes=_age_minutes(snapshot.observed_at),
            freshness="stale" if (stale or stale_measurement) else "fresh",
            stale=stale or stale_measurement,
            station=_station_from_raw(station_raw),
            attribution=(
                [str(item) for item in attribution]
                if isinstance(attribution, list) and attribution
                else [snapshot.provider]
            ),
        ),
    )


def _forecast_from_provider(
    forecast: ProviderForecast, *, requested: AirLocation, hours: int
) -> AirForecast:
    return AirForecast(
        location=requested,
        hourly=[
            ForecastPoint(
                time=point.time,
                pm2_5=point.pm2_5,
                pm10=point.pm10,
                no2_ug_m3=point.no2_ug_m3,
                o3_ug_m3=point.o3_ug_m3,
                co_ug_m3=point.co_ug_m3,
                so2_ug_m3=point.so2_ug_m3,
            )
            for point in forecast.points[:hours]
        ],
        provenance=Provenance(
            provider=forecast.provider,
            kind="modelled",
            source_type=_source_type(forecast.source_type, "model_forecast"),
            model=forecast.model,
            observed_at=None,
            fetched_at=forecast.issued_at,
            age_minutes=_age_minutes(forecast.issued_at),
            stale=False,
            attribution=list(forecast.attribution),
        ),
    )


def _series_payload(forecast: ProviderForecast) -> dict[str, Any]:
    return {
        "provider": forecast.provider,
        "source_type": forecast.source_type,
        "issued_at": forecast.issued_at.isoformat(),
        "points": [
            {
                "time": point.time.isoformat(),
                "pm2_5": point.pm2_5,
                "pm10": point.pm10,
                "no2_ug_m3": point.no2_ug_m3,
                "o3_ug_m3": point.o3_ug_m3,
                "co_ug_m3": point.co_ug_m3,
                "so2_ug_m3": point.so2_ug_m3,
            }
            for point in forecast.points
        ],
        "attribution": list(forecast.attribution),
        "model": forecast.model,
    }


def _forecast_from_series(
    series: Any,
    *,
    requested: AirLocation,
    hours: int,
    stale: bool,
    default_provider: str,
) -> AirForecast | None:
    if not isinstance(series, dict):
        return None
    raw_points = series.get("points")
    if not isinstance(raw_points, list) or not raw_points:
        return None
    points: list[ForecastPoint] = []
    for raw in raw_points:
        if not isinstance(raw, dict):
            continue
        try:
            points.append(ForecastPoint.model_validate(raw))
        except ValueError:
            continue
        if len(points) >= hours:
            break
    if not points:
        return None
    issued_raw = series.get("issued_at")
    try:
        issued_at = (
            datetime.fromisoformat(issued_raw)
            if isinstance(issued_raw, str)
            else points[0].time
        )
    except ValueError:
        issued_at = points[0].time
    attribution = series.get("attribution")
    model = series.get("model")
    provider = series.get("provider")
    source_type = series.get("source_type")
    return AirForecast(
        location=requested,
        hourly=points,
        provenance=Provenance(
            provider=provider if isinstance(provider, str) else default_provider,
            kind="modelled",
            source_type=_source_type(
                source_type if isinstance(source_type, str) else None,
                "modelled",
            ),
            model=model if isinstance(model, str) else None,
            observed_at=None,
            fetched_at=issued_at,
            age_minutes=_age_minutes(issued_at),
            stale=stale,
            attribution=(
                [str(item) for item in attribution]
                if isinstance(attribution, list) and attribution
                else [default_provider]
            ),
        ),
    )


def _snapshot_raw(reading: ProviderReading) -> dict[str, Any]:
    raw = dict(reading.raw or {})
    raw.update(
        {
            "source_type": _source_type(reading.source_type, reading.kind),
            "model": reading.model,
            "timezone": reading.timezone,
            "attribution": list(reading.attribution),
            "quality_flags": list(reading.quality_flags),
            "units": reading.units,
            "station": (
                {
                    "id": reading.station.id,
                    "name": reading.station.name,
                    "provider": reading.station.provider,
                    "latitude": reading.station.latitude,
                    "longitude": reading.station.longitude,
                    "distance_km": reading.station.distance_km,
                    "timezone": reading.station.timezone,
                    "is_monitor": reading.station.is_monitor,
                }
                if reading.station
                else None
            ),
            "aqi": {
                "averages": reading.averages,
                "windows": {
                    pollutant: {
                        "window": detail.window,
                        "hours": detail.hours,
                        "valid_hours": detail.valid_hours,
                        "required_hours": detail.required_hours,
                        "method": detail.method,
                    }
                    for pollutant, detail in reading.average_windows.items()
                },
            },
        }
    )
    return raw


def _windows_from_raw(value: object) -> dict[str, AveragingDetail]:
    if not isinstance(value, dict):
        return {}
    windows: dict[str, AveragingDetail] = {}
    for pollutant, raw in value.items():
        if not isinstance(pollutant, str) or not isinstance(raw, dict):
            continue
        window = raw.get("window")
        hours = raw.get("hours")
        valid = raw.get("valid_hours")
        required = raw.get("required_hours")
        method = raw.get("method")
        if (
            isinstance(window, str)
            and isinstance(hours, int)
            and isinstance(valid, int)
            and isinstance(required, int)
            and isinstance(method, str)
        ):
            windows[pollutant] = AveragingDetail(
                window=window,
                hours=hours,
                valid_hours=valid,
                required_hours=required,
                value=None,
                method=method,
            )
    return windows


def _station_from_raw(value: object) -> StationSchema | None:
    if not isinstance(value, dict):
        return None
    try:
        return StationSchema.model_validate(value)
    except ValueError:
        return None


def _fallback_health(provider: AirQualityProvider) -> ProviderHealth:
    source_type = _source_type(
        getattr(provider, "source_type", None),
        "measured" if getattr(provider, "kind", None) == "measured" else "modelled",
    )
    attribution = getattr(provider, "attribution", None)
    return ProviderHealth(
        name=provider.name,
        status="ok",
        configured=True,
        source_type=source_type,
        supports_forecast=bool(getattr(provider, "supports_forecast", True)),
        supports_history=bool(getattr(provider, "supports_history", True)),
        supports_stations=bool(getattr(provider, "supports_stations", False)),
        attribution=(
            tuple(str(item) for item in attribution)
            if isinstance(attribution, tuple)
            else (provider.name,)
        ),
        detail=f"{provider.name} did not report a detailed health status.",
    )
