"""Generated plans and advice."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.profile import utc_now


class Routine(Base):
    __tablename__ = "routines"
    __table_args__ = (
        CheckConstraint("char_length(inputs_hash) = 64", name="inputs_hash_length"),
        CheckConstraint("btrim(timezone) <> ''", name="timezone_present"),
        CheckConstraint("btrim(engine_version) <> ''", name="engine_version_present"),
        CheckConstraint("version >= 1", name="version_positive"),
        CheckConstraint("status IN ('active','superseded')", name="status_allowed"),
        CheckConstraint("expires_at > generated_at", name="expiry_after_generated"),
        UniqueConstraint(
            "household_id",
            "plan_date",
            "inputs_hash",
            "version",
            name="uq_routines_identity",
        ),
        Index("ix_routines_household_date", "household_id", "plan_date"),
        Index("ix_routines_household_status", "household_id", "status"),
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
    plan_date: Mapped[date] = mapped_column(Date, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    inputs_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    plan: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active", server_default=text("'active'")
    )
    parent_routine_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("routines.id", ondelete="SET NULL")
    )
    generated_at: Mapped[datetime] = mapped_column(
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
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


_ROUTINE_CATEGORIES = (
    "'morning_walk','outdoor_sports','school_travel','college_travel',"
    "'office_commute','grocery_shopping','outdoor_recreation','indoor_exercise',"
    "'household_activity','gardening','other'"
)


class RoutineActivity(Base):
    """Household-level activity preferences used by the planner."""

    __tablename__ = "routine_activities"
    __table_args__ = (
        CheckConstraint("btrim(title) <> ''", name="title_present"),
        CheckConstraint(
            f"category IN ({_ROUTINE_CATEGORIES})", name="category_allowed"
        ),
        CheckConstraint("duration_min BETWEEN 15 AND 240", name="duration_range"),
        CheckConstraint(
            "preferred_start ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'",
            name="preferred_start_format",
        ),
        CheckConstraint(
            "earliest_start IS NULL OR earliest_start"
            " ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'",
            name="earliest_start_format",
        ),
        CheckConstraint(
            "latest_start IS NULL OR latest_start"
            " ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'",
            name="latest_start_format",
        ),
        CheckConstraint("venue IN ('indoor','outdoor')", name="venue_allowed"),
        CheckConstraint("priority IN ('low','medium','high')", name="priority_allowed"),
        CheckConstraint(
            "intensity IN ('light','moderate','vigorous')", name="intensity_allowed"
        ),
        Index("ix_routine_activities_household", "household_id", "active"),
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
    title: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    preferred_start: Mapped[str] = mapped_column(String(5), nullable=False)
    earliest_start: Mapped[str | None] = mapped_column(String(5))
    latest_start: Mapped[str | None] = mapped_column(String(5))
    venue: Mapped[str] = mapped_column(String(16), nullable=False)
    fixed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    priority: Mapped[str] = mapped_column(
        String(8), nullable=False, default="medium", server_default=text("'medium'")
    )
    intensity: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="moderate",
        server_default=text("'moderate'"),
    )
    member_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    location: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    indoor_alternative: Mapped[str | None] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
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


class RoutineItem(Base):
    """Normalised snapshot of the activities assigned to one stored plan."""

    __tablename__ = "routine_items"
    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled','unscheduled','cancelled','done','skipped')",
            name="status_allowed",
        ),
        CheckConstraint(
            "start_at IS NULL OR end_at IS NULL OR end_at > start_at",
            name="end_after_start",
        ),
        UniqueConstraint("routine_id", "activity_id", name="uq_routine_items_activity"),
        Index("ix_routine_items_routine", "routine_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    routine_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("routines.id", ondelete="CASCADE"),
        nullable=False,
    )
    activity_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    title: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    venue: Mapped[str] = mapped_column(String(16), nullable=False)
    priority: Mapped[str] = mapped_column(String(8), nullable=False)
    fixed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_min: Mapped[int | None] = mapped_column(Integer)
    override: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    rationale: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    context: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    alternatives: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
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


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        CheckConstraint(
            "module IN ('air','family','routine','indoor','ecoroute','impact','copilot')",
            name="module_allowed",
        ),
        CheckConstraint(
            "severity IN ('good','satisfactory','moderate','poor','very_poor','severe','info')",
            name="severity_allowed",
        ),
        CheckConstraint("source IN ('deterministic','ai')", name="source_allowed"),
        CheckConstraint("btrim(title) <> ''", name="title_present"),
        CheckConstraint("btrim(body) <> ''", name="body_present"),
        CheckConstraint(
            "dismissed_at IS NULL OR dismissed_at >= created_at",
            name="dismissed_after_created",
        ),
        CheckConstraint(
            "rule_id IS NULL OR btrim(rule_id) <> ''",
            name="rule_id_present",
        ),
        Index("ix_recs_household_created", "household_id", "created_at"),
        Index("ix_recs_routine", "routine_id"),
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
    routine_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("routines.id", ondelete="SET NULL")
    )
    module: Mapped[str] = mapped_column(String(16), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(String(2000), nullable=False)
    fact_refs: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    rule_id: Mapped[str | None] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    model: Mapped[str | None] = mapped_column(String(80))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
