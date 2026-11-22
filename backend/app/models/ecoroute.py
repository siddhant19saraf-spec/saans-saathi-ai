"""Eco-route journey and emission calculation models."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
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


class SavedJourney(Base):
    """A user-saved eco-route journey comparison."""

    __tablename__ = "saved_journeys"
    __table_args__ = (
        CheckConstraint("distance_km >= 0", name="journey_distance_non_negative"),
        CheckConstraint("duration_min >= 0", name="journey_duration_non_negative"),
        CheckConstraint("passengers >= 1", name="journey_passengers_positive"),
        Index("ix_saved_journeys_household_created", "household_id", "created_at"),
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
    origin_lat: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    origin_lon: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    destination_lat: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    destination_lon: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    travel_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    modes: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    selected_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    passengers: Mapped[int] = mapped_column(nullable=False, server_default=text("1"))
    distance_km: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    duration_min: Mapped[int] = mapped_column(nullable=False, server_default=text("0"))
    co2e_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    co2e_per_passenger_kg: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )


class EmissionCalculation(Base):
    """A stored emissions calculation with full factor provenance."""

    __tablename__ = "emission_calculations"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="calculation_quantity_non_negative"),
        CheckConstraint("result_kg_co2e >= 0", name="calculation_result_non_negative"),
        CheckConstraint("factor_value >= 0", name="calculation_factor_non_negative"),
        Index("ix_calculations_household_created", "household_id", "created_at"),
        Index("ix_calculations_activity_type", "household_id", "activity_type"),
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
    activity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    result_kg_co2e: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    factor_key: Mapped[str] = mapped_column(String(64), nullable=False)
    factor_value: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    factor_unit: Mapped[str] = mapped_column(String(32), nullable=False)
    factor_version: Mapped[str] = mapped_column(String(32), nullable=False)
    factor_source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    calculation_method: Mapped[str] = mapped_column(String(200), nullable=False)
    assumptions: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )


class SustainabilityGoal(Base):
    """A user-defined sustainability goal with progress tracking."""

    __tablename__ = "sustainability_goals"
    __table_args__ = (
        CheckConstraint("target_value > 0", name="goal_target_positive"),
        CheckConstraint("current_value >= 0", name="goal_current_non_negative"),
        Index("ix_goals_household_active", "household_id", "is_active"),
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
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    activity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    target_value: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    current_value: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), nullable=False, server_default=text("0")
    )
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))
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
        server_default=func.now(),
    )

    @property
    def progress_percent(self) -> float | None:
        if self.target_value <= 0:
            return None
        return round(
            min(100.0, float(self.current_value) / float(self.target_value) * 100.0), 1
        )

    @property
    def is_complete(self) -> bool:
        return self.current_value >= self.target_value


__all__ = ["EmissionCalculation", "SavedJourney", "SustainabilityGoal"]
