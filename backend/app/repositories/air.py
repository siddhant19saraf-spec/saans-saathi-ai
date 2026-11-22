"""Air-quality cache and usage persistence."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.air import AirQualityFetchLog, AirQualityForecast, AirQualitySnapshot
from app.models.impact import UsageDaily


def key_for(value: float) -> Decimal:
    return Decimal(str(round(value, 2)))


async def latest_snapshot(
    session: AsyncSession,
    *,
    provider: str,
    lat_key: Decimal,
    lon_key: Decimal,
    max_age: timedelta,
) -> AirQualitySnapshot | None:
    since = datetime.now(tz=UTC) - max_age
    statement = (
        select(AirQualitySnapshot)
        .where(
            AirQualitySnapshot.provider == provider,
            AirQualitySnapshot.lat_key == lat_key,
            AirQualitySnapshot.lon_key == lon_key,
            AirQualitySnapshot.fetched_at >= since,
        )
        .order_by(AirQualitySnapshot.fetched_at.desc())
        .limit(1)
    )
    return await session.scalar(statement)


async def upsert_snapshot(
    session: AsyncSession,
    *,
    provider: str,
    lat_key: Decimal,
    lon_key: Decimal,
    kind: str,
    observed_at: datetime,
    fetched_at: datetime,
    expires_at: datetime,
    values: dict[str, float | None],
    us_aqi: int | None,
    eu_aqi: int | None,
    raw: dict[str, Any],
    source_type: str = "model_forecast",
    station_name: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "provider": provider,
        "lat_key": lat_key,
        "lon_key": lon_key,
        "kind": kind,
        "source_type": source_type,
        "observed_at": observed_at,
        "fetched_at": fetched_at,
        "expires_at": expires_at,
        "pm2_5": values.get("pm2_5"),
        "pm10": values.get("pm10"),
        "co_ug_m3": values.get("co_ug_m3"),
        "no2_ug_m3": values.get("no2_ug_m3"),
        "so2_ug_m3": values.get("so2_ug_m3"),
        "o3_ug_m3": values.get("o3_ug_m3"),
        "dust_ug_m3": values.get("dust_ug_m3"),
        "us_aqi": us_aqi,
        "eu_aqi": eu_aqi,
        "station_name": station_name,
        "raw": raw,
    }
    statement = pg_insert(AirQualitySnapshot).values(**payload)
    statement = statement.on_conflict_do_update(
        index_elements=[
            AirQualitySnapshot.provider,
            AirQualitySnapshot.lat_key,
            AirQualitySnapshot.lon_key,
            AirQualitySnapshot.observed_at,
        ],
        set_={
            key: payload[key]
            for key in payload
            if key not in {"provider", "lat_key", "lon_key", "observed_at"}
        },
    )
    await session.execute(statement)


async def latest_forecast(
    session: AsyncSession,
    *,
    provider: str,
    lat_key: Decimal,
    lon_key: Decimal,
    max_age: timedelta,
) -> AirQualityForecast | None:
    since = datetime.now(tz=UTC) - max_age
    statement = (
        select(AirQualityForecast)
        .where(
            AirQualityForecast.provider == provider,
            AirQualityForecast.lat_key == lat_key,
            AirQualityForecast.lon_key == lon_key,
            AirQualityForecast.issued_at >= since,
        )
        .order_by(AirQualityForecast.issued_at.desc())
        .limit(1)
    )
    return await session.scalar(statement)


async def upsert_forecast(
    session: AsyncSession,
    *,
    provider: str,
    lat_key: Decimal,
    lon_key: Decimal,
    issued_at: datetime,
    series: dict[str, Any],
    expires_at: datetime,
) -> None:
    payload = {
        "provider": provider,
        "lat_key": lat_key,
        "lon_key": lon_key,
        "issued_at": issued_at,
        "series": series,
        "expires_at": expires_at,
    }
    statement = pg_insert(AirQualityForecast).values(**payload)
    statement = statement.on_conflict_do_update(
        index_elements=[
            AirQualityForecast.provider,
            AirQualityForecast.lat_key,
            AirQualityForecast.lon_key,
            AirQualityForecast.issued_at,
        ],
        set_={"series": series, "expires_at": expires_at},
    )
    await session.execute(statement)


async def log_fetch(
    session: AsyncSession,
    *,
    provider: str,
    status: str,
    http_status: int | None = None,
    latency_ms: int | None = None,
    lat_key: Decimal | None = None,
    lon_key: Decimal | None = None,
) -> None:
    session.add(
        AirQualityFetchLog(
            provider=provider,
            status=status,
            http_status=http_status,
            latency_ms=latency_ms,
            lat_key=lat_key,
            lon_key=lon_key,
        )
    )
    await session.flush()


async def consume_budget(
    session: AsyncSession,
    *,
    key: str,
    budget: int,
    day: date,
) -> bool:
    """Atomically count one upstream call, refusing beyond the daily budget."""
    if budget <= 0:
        return False
    insert = pg_insert(UsageDaily).values(day=day, key=key, requests=1)
    statement = insert.on_conflict_do_update(
        index_elements=[UsageDaily.day, UsageDaily.key],
        set_={"requests": UsageDaily.requests + 1},
        where=UsageDaily.requests < budget,
    ).returning(UsageDaily.requests)
    result = await session.scalar(statement)
    return result is not None


async def read_budget(session: AsyncSession, *, key: str, day: date) -> int:
    used = await session.scalar(
        select(UsageDaily.requests).where(UsageDaily.day == day, UsageDaily.key == key)
    )
    return int(used or 0)
