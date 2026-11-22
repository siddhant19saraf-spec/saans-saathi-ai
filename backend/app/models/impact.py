"""Sustainability activity ledger, metered usage and privacy audit events."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.profile import utc_now


class SustainabilityActivity(Base):
    __tablename__ = "sustainability_activities"
    __table_args__ = (
        CheckConstraint(
            "activity_type IN ('walked','public-transport','worked-from-home','planted-tree')",
            name="activity_type_allowed",
        ),
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        CheckConstraint("co2e_kg >= 0", name="co2e_non_negative"),
        CheckConstraint("factor_value >= 0", name="factor_value_non_negative"),
        CheckConstraint("unit IN ('km','days','trees')", name="unit_allowed"),
        CheckConstraint("btrim(factor_key) <> ''", name="factor_key_present"),
        CheckConstraint("btrim(factor_unit) <> ''", name="factor_unit_present"),
        CheckConstraint("btrim(factor_version) <> ''", name="factor_version_present"),
        CheckConstraint("btrim(factor_source_url) <> ''", name="factor_source_present"),
        Index("ix_activities_household_date", "household_id", "occurred_on"),
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
    activity_type: Mapped[str] = mapped_column(String(24), nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False)
    co2e_kg: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    factor_key: Mapped[str] = mapped_column(String(64), nullable=False)
    factor_value: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    factor_unit: Mapped[str] = mapped_column(String(32), nullable=False)
    factor_version: Mapped[str] = mapped_column(String(32), nullable=False)
    factor_source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )


class UsageDaily(Base):
    __tablename__ = "usage_daily"
    __table_args__ = (
        CheckConstraint("requests >= 0", name="requests_non_negative"),
        CheckConstraint("input_tokens >= 0", name="input_tokens_non_negative"),
        CheckConstraint("output_tokens >= 0", name="output_tokens_non_negative"),
    )

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    key: Mapped[str] = mapped_column(String(32), primary_key=True)
    requests: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    input_tokens: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default=text("0")
    )
    output_tokens: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default=text("0")
    )


class PrivacyEvent(Base):
    __tablename__ = "privacy_events"
    __table_args__ = (
        CheckConstraint(
            "event IN ('consent','delete_all','data_export')",
            name="event_allowed",
        ),
        Index("ix_privacy_events_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    profile_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="SET NULL")
    )
    event: Mapped[str] = mapped_column(String(24), nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
