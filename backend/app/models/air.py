"""Air-quality cache, forecast cache and provider fetch audit log."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Float,
    Identity,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.profile import utc_now


class AirQualitySnapshot(Base):
    __tablename__ = "air_quality_snapshots"
    __table_args__ = (
        CheckConstraint("kind IN ('modelled','measured')", name="kind_allowed"),
        CheckConstraint(
            "source_type IN"
            " ('ground_observation','model_forecast','historical_observation')",
            name="source_type_allowed",
        ),
        CheckConstraint("lat_key BETWEEN -90 AND 90", name="lat_key_range"),
        CheckConstraint("lon_key BETWEEN -180 AND 180", name="lon_key_range"),
        CheckConstraint("expires_at > fetched_at", name="expiry_after_fetch"),
        CheckConstraint(
            "(pm2_5 IS NULL OR pm2_5 >= 0)"
            " AND (pm10 IS NULL OR pm10 >= 0)"
            " AND (co_ug_m3 IS NULL OR co_ug_m3 >= 0)"
            " AND (no2_ug_m3 IS NULL OR no2_ug_m3 >= 0)"
            " AND (so2_ug_m3 IS NULL OR so2_ug_m3 >= 0)"
            " AND (o3_ug_m3 IS NULL OR o3_ug_m3 >= 0)"
            " AND (dust_ug_m3 IS NULL OR dust_ug_m3 >= 0)",
            name="pollutants_non_negative",
        ),
        CheckConstraint("us_aqi IS NULL OR us_aqi >= 0", name="us_aqi_non_negative"),
        CheckConstraint("eu_aqi IS NULL OR eu_aqi >= 0", name="eu_aqi_non_negative"),
        CheckConstraint(
            "station_distance_km IS NULL OR station_distance_km >= 0",
            name="station_distance_non_negative",
        ),
        UniqueConstraint(
            "provider",
            "lat_key",
            "lon_key",
            "observed_at",
            name="uq_air_snapshots_identity",
        ),
        Index("ix_snap_lookup", "lat_key", "lon_key", "observed_at"),
        Index("ix_snap_expiry", "expires_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    lat_key: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    lon_key: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
        default="model_forecast",
        server_default="model_forecast",
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    pm2_5: Mapped[float | None] = mapped_column(Float)
    pm10: Mapped[float | None] = mapped_column(Float)
    co_ug_m3: Mapped[float | None] = mapped_column(Float)
    no2_ug_m3: Mapped[float | None] = mapped_column(Float)
    so2_ug_m3: Mapped[float | None] = mapped_column(Float)
    o3_ug_m3: Mapped[float | None] = mapped_column(Float)
    dust_ug_m3: Mapped[float | None] = mapped_column(Float)
    us_aqi: Mapped[int | None] = mapped_column(SmallInteger)
    eu_aqi: Mapped[int | None] = mapped_column(SmallInteger)
    station_id: Mapped[str | None] = mapped_column(String(80))
    station_name: Mapped[str | None] = mapped_column(String(160))
    station_distance_km: Mapped[float | None] = mapped_column(Float)
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class AirQualityForecast(Base):
    __tablename__ = "air_quality_forecasts"
    __table_args__ = (
        CheckConstraint("lat_key BETWEEN -90 AND 90", name="lat_key_range"),
        CheckConstraint("lon_key BETWEEN -180 AND 180", name="lon_key_range"),
        CheckConstraint("expires_at > issued_at", name="expiry_after_issue"),
        UniqueConstraint(
            "provider",
            "lat_key",
            "lon_key",
            "issued_at",
            name="uq_air_forecasts_identity",
        ),
        Index("ix_forecast_lookup", "lat_key", "lon_key", "issued_at"),
        Index("ix_forecast_expiry", "expires_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    lat_key: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    lon_key: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    series: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class AirQualityFetchLog(Base):
    __tablename__ = "air_quality_fetch_log"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ok','timeout','http_error','parse_error','circuit_open',"
            "'rate_limited','unauthorized','not_configured','not_found','unsupported')",
            name="status_allowed",
        ),
        CheckConstraint(
            "http_status IS NULL OR http_status BETWEEN 100 AND 599",
            name="http_status_range",
        ),
        CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0",
            name="latency_non_negative",
        ),
        CheckConstraint(
            "lat_key IS NULL OR lat_key BETWEEN -90 AND 90",
            name="lat_key_range",
        ),
        CheckConstraint(
            "lon_key IS NULL OR lon_key BETWEEN -180 AND 180",
            name="lon_key_range",
        ),
        Index("ix_fetch_log_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    http_status: Mapped[int | None] = mapped_column(SmallInteger)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    lat_key: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    lon_key: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
