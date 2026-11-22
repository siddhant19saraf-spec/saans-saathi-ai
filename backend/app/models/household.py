"""Household context: location, members, preferences and saved places."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.profile import utc_now


class Household(Base):
    __tablename__ = "households"
    __table_args__ = (
        CheckConstraint("lat BETWEEN -90 AND 90", name="lat_range"),
        CheckConstraint("lon BETWEEN -180 AND 180", name="lon_range"),
        CheckConstraint(
            "dwelling IN ('apartment_ground','apartment_upper','independent','other')",
            name="dwelling_allowed",
        ),
        CheckConstraint(
            "cooking_fuel IN ('lpg','png','induction','biomass','mixed','other')",
            name="cooking_fuel_allowed",
        ),
        CheckConstraint(
            "purifier_cadr IS NULL OR purifier_cadr BETWEEN 50 AND 1500",
            name="purifier_cadr_range",
        ),
        CheckConstraint(
            "room_area_m2 IS NULL OR room_area_m2 BETWEEN 5 AND 300",
            name="room_area_range",
        ),
        CheckConstraint(
            "ceiling_m IS NULL OR ceiling_m BETWEEN 2.0 AND 5.0",
            name="ceiling_range",
        ),
        CheckConstraint("btrim(timezone) <> ''", name="timezone_present"),
        CheckConstraint("btrim(name) <> ''", name="name_present"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    profile_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    name: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="Household",
        server_default=text("'Household'"),
    )
    lat: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    lon: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    city: Mapped[str | None] = mapped_column(String(120))
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, default="Asia/Kolkata"
    )
    dwelling: Mapped[str] = mapped_column(String(24), nullable=False)
    cooking_fuel: Mapped[str] = mapped_column(String(16), nullable=False)
    has_purifier: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    purifier_cadr: Mapped[int | None] = mapped_column(Integer)
    room_area_m2: Mapped[int | None] = mapped_column(Integer)
    ceiling_m: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now(),
    )


class HouseholdMember(Base):
    __tablename__ = "household_members"
    __table_args__ = (
        CheckConstraint(
            "age_band IN ('0-5','6-12','13-17','18-59','60+')",
            name="age_band_allowed",
        ),
        CheckConstraint(
            "health_flags <@ ARRAY['asthma','allergy','copd','heart','pregnant']",
            name="health_flags_allowed",
        ),
        Index("ix_members_household", "household_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    household_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
    )
    age_band: Mapped[str] = mapped_column(String(8), nullable=False)
    health_flags: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list,
        server_default=text("'{}'::text[]"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )


class HouseholdPreference(Base):
    __tablename__ = "household_preferences"
    __table_args__ = (
        CheckConstraint(
            "alert_threshold_aqi BETWEEN 0 AND 500",
            name="alert_threshold_range",
        ),
        CheckConstraint("btrim(locale) <> ''", name="locale_present"),
        CheckConstraint(
            "transport_mode IN ('walk','cycle','public','private','mixed')",
            name="transport_mode_allowed",
        ),
        CheckConstraint(
            "quiet_hours_start IS NULL OR quiet_hours_start"
            " ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'",
            name="quiet_hours_start_format",
        ),
        CheckConstraint(
            "quiet_hours_end IS NULL OR quiet_hours_end"
            " ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'",
            name="quiet_hours_end_format",
        ),
    )

    household_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("households.id", ondelete="CASCADE"),
        primary_key=True,
    )
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="en-IN")
    activity_windows: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    alert_threshold_aqi: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=150, server_default=text("150")
    )
    transport_mode: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="mixed",
        server_default=text("'mixed'"),
    )
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    notify_alerts: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    notify_daily_summary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    quiet_hours_start: Mapped[str | None] = mapped_column(String(5))
    quiet_hours_end: Mapped[str | None] = mapped_column(String(5))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now(),
    )


class SavedLocation(Base):
    __tablename__ = "saved_locations"
    __table_args__ = (
        CheckConstraint("lat BETWEEN -90 AND 90", name="lat_range"),
        CheckConstraint("lon BETWEEN -180 AND 180", name="lon_range"),
        CheckConstraint(
            "kind IN ('home','work','school','other')", name="kind_allowed"
        ),
        CheckConstraint("btrim(label) <> ''", name="label_present"),
        UniqueConstraint(
            "household_id", "label", name="uq_saved_locations_household_label"
        ),
        Index("ix_saved_locations_household", "household_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    household_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(60), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default="other")
    lat: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    lon: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
