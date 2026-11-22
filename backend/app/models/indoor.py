"""IndoorShield assessments, sensors, readings and action plans.

Measured indoor samples live in ``indoor_sensor_readings``. Everything the
deterministic engine derives from a questionnaire lives in
``indoor_recommendations`` and is explicitly a recommendation, not a
measurement.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
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

_ROOM_TYPES = (
    "'living_room','bedroom','kitchen','bathroom','study','children_room','other'"
)
_VENTILATION = "'windows','exhaust','mechanical','none','other'"
_DAMPNESS = "'none','occasional','persistent','unknown'"
_SOURCE_CODES = (
    "'biomass_cooking','gas_stove','cooking_fumes','candles_incense',"
    "'tobacco_smoke','indoor_burning','cleaning_products','aerosol_sprays',"
    "'paints_solvents','renovation_materials','dust','outdoor_infiltration',"
    "'poor_ventilation','dampness','mold_risk','other'"
)
_SOURCE_FREQUENCY = "'once','occasional','weekly','daily','frequent'"
_POLLUTANTS = "'pm2_5','pm10','co2','co','tvoc','humidity'"


class IndoorAssessment(Base):
    """A completed IndoorShield home assessment owned by one household."""

    __tablename__ = "indoor_assessments"
    __table_args__ = (
        CheckConstraint("status IN ('draft','completed')", name="status_allowed"),
        CheckConstraint(
            "dwelling IN ('apartment_ground','apartment_upper','independent','other')",
            name="dwelling_allowed",
        ),
        CheckConstraint(
            "cooking_fuel IN ('lpg','png','induction','biomass','mixed','other')",
            name="cooking_fuel_allowed",
        ),
        CheckConstraint(
            "cooking_location IN ('indoor_kitchen','separate_room','outdoor','other')",
            name="cooking_location_allowed",
        ),
        CheckConstraint(
            "cleaning_frequency IN ('daily','weekly','monthly','less')",
            name="cleaning_frequency_allowed",
        ),
        CheckConstraint(
            "confidence IS NULL OR confidence IN ('high','medium','low')",
            name="confidence_allowed",
        ),
        CheckConstraint(
            "engine_version IS NULL OR btrim(engine_version) <> ''",
            name="engine_version_present",
        ),
        CheckConstraint(
            "notes IS NULL OR char_length(notes) <= 500", name="notes_length"
        ),
        Index("ix_indoor_assessments_household", "household_id", "created_at"),
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
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="completed",
        server_default=text("'completed'"),
    )
    dwelling: Mapped[str] = mapped_column(String(24), nullable=False)
    cooking_fuel: Mapped[str] = mapped_column(String(16), nullable=False)
    cooking_location: Mapped[str] = mapped_column(String(24), nullable=False)
    cooking_exhaust: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    cleaning_frequency: Mapped[str] = mapped_column(String(16), nullable=False)
    sensor_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    notes: Mapped[str | None] = mapped_column(String(500))
    engine_version: Mapped[str | None] = mapped_column(String(32))
    summary: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[str | None] = mapped_column(String(16))
    assumptions: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    limitations: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    outdoor_context: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    explanation: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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


class IndoorRoom(Base):
    __tablename__ = "indoor_rooms"
    __table_args__ = (
        CheckConstraint("btrim(name) <> ''", name="name_present"),
        CheckConstraint(f"room_type IN ({_ROOM_TYPES})", name="room_type_allowed"),
        CheckConstraint("area_m2 BETWEEN 3 AND 500", name="area_range"),
        CheckConstraint("ceiling_m BETWEEN 2.0 AND 6.0", name="ceiling_range"),
        CheckConstraint(f"ventilation IN ({_VENTILATION})", name="ventilation_allowed"),
        CheckConstraint("windows_count BETWEEN 0 AND 20", name="windows_range"),
        CheckConstraint(
            "purifier_cadr IS NULL OR purifier_cadr BETWEEN 0 AND 1500",
            name="purifier_cadr_range",
        ),
        CheckConstraint(f"dampness IN ({_DAMPNESS})", name="dampness_allowed"),
        CheckConstraint(
            "purifier_cadr IS NULL OR has_purifier", name="cadr_requires_purifier"
        ),
        Index("ix_indoor_rooms_assessment", "assessment_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    assessment_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("indoor_assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    room_type: Mapped[str] = mapped_column(String(24), nullable=False)
    area_m2: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False)
    ceiling_m: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    ventilation: Mapped[str] = mapped_column(String(16), nullable=False)
    windows_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    has_purifier: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    purifier_cadr: Mapped[int | None] = mapped_column(Integer)
    dampness: Mapped[str] = mapped_column(
        String(16), nullable=False, default="unknown", server_default=text("'unknown'")
    )
    position: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )


class IndoorSource(Base):
    __tablename__ = "indoor_sources"
    __table_args__ = (
        CheckConstraint(f"code IN ({_SOURCE_CODES})", name="code_allowed"),
        CheckConstraint(
            f"frequency IN ({_SOURCE_FREQUENCY})", name="frequency_allowed"
        ),
        CheckConstraint("note IS NULL OR char_length(note) <= 200", name="note_length"),
        UniqueConstraint("assessment_id", "code", name="uq_indoor_sources_code"),
        Index("ix_indoor_sources_assessment", "assessment_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    assessment_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("indoor_assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    frequency: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="occasional",
        server_default=text("'occasional'"),
    )
    note: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )


class IndoorSensor(Base):
    """A registered indoor device.

    The provider and external identifier are supplied by the integration that
    owns the device. No row is created automatically, so the UI can truthfully
    show that indoor sensor data is unavailable until one is connected.
    """

    __tablename__ = "indoor_sensors"
    __table_args__ = (
        CheckConstraint("btrim(provider) <> ''", name="provider_present"),
        CheckConstraint("btrim(external_id) <> ''", name="external_id_present"),
        CheckConstraint("btrim(name) <> ''", name="name_present"),
        CheckConstraint(
            "calibration_status IN ('verified','unverified','unknown')",
            name="calibration_allowed",
        ),
        CheckConstraint("status IN ('active','inactive')", name="status_allowed"),
        UniqueConstraint("provider", "external_id", name="uq_indoor_sensors_identity"),
        Index("ix_indoor_sensors_household", "household_id", "status"),
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
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    external_id: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str | None] = mapped_column(String(80))
    room_name: Mapped[str | None] = mapped_column(String(60))
    calibration_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="unknown", server_default=text("'unknown'")
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active", server_default=text("'active'")
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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


class IndoorSensorReading(Base):
    """One validated measurement reported by a registered device.

    Values are never synthesised by the application. ``quality_status`` marks
    whether the integration accepted the sample; only ``valid`` samples reach
    the deterministic rule engine.
    """

    __tablename__ = "indoor_sensor_readings"
    __table_args__ = (
        CheckConstraint(f"pollutant IN ({_POLLUTANTS})", name="pollutant_allowed"),
        CheckConstraint("value >= 0", name="value_non_negative"),
        CheckConstraint("btrim(unit) <> ''", name="unit_present"),
        CheckConstraint(
            "calibration_status IN ('verified','unverified','unknown')",
            name="calibration_allowed",
        ),
        CheckConstraint(
            "quality_status IN ('valid','suspect')", name="quality_allowed"
        ),
        UniqueConstraint(
            "sensor_id",
            "pollutant",
            "measured_at",
            name="uq_indoor_readings_identity",
        ),
        Index(
            "ix_indoor_readings_sensor_pollutant",
            "sensor_id",
            "pollutant",
            "measured_at",
        ),
        Index("ix_indoor_readings_household", "household_id", "measured_at"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    sensor_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("indoor_sensors.id", ondelete="CASCADE"),
        nullable=False,
    )
    household_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
    )
    pollutant: Mapped[str] = mapped_column(String(16), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False)
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
    calibration_status: Mapped[str] = mapped_column(String(16), nullable=False)
    quality_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="valid", server_default=text("'valid'")
    )
    note: Mapped[str | None] = mapped_column(String(200))


class IndoorRecommendation(Base):
    """A persisted deterministic action belonging to one assessment."""

    __tablename__ = "indoor_recommendations"
    __table_args__ = (
        CheckConstraint(
            "category IN ('cooking','cleaning','dust','ventilation','filtration',"
            "'humidity','outdoor_pollution','general')",
            name="category_allowed",
        ),
        CheckConstraint("priority IN ('high','medium','low')", name="priority_allowed"),
        CheckConstraint("priority_score BETWEEN 0 AND 1000", name="score_range"),
        CheckConstraint(
            "status IN ('pending','completed','dismissed')", name="status_allowed"
        ),
        CheckConstraint("source IN ('deterministic','ai')", name="source_allowed"),
        CheckConstraint("btrim(rule_id) <> ''", name="rule_id_present"),
        CheckConstraint(
            "frequency IN ('once','daily','weekly','monthly')",
            name="frequency_allowed",
        ),
        CheckConstraint(
            "completed_at IS NULL OR status = 'completed'",
            name="completed_requires_status",
        ),
        Index(
            "ix_indoor_recommendations_assessment",
            "assessment_id",
            "status",
        ),
        Index(
            "ix_indoor_recommendations_household",
            "household_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    assessment_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("indoor_assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    household_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
    )
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(24), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    issue: Mapped[str] = mapped_column(String(500), nullable=False)
    action: Mapped[str] = mapped_column(String(1000), nullable=False)
    priority: Mapped[str] = mapped_column(String(8), nullable=False)
    priority_score: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence: Mapped[str] = mapped_column(String(500), nullable=False)
    expected_benefit: Mapped[str] = mapped_column(String(500), nullable=False)
    limitations: Mapped[str] = mapped_column(String(700), nullable=False)
    frequency: Mapped[str] = mapped_column(String(16), nullable=False)
    source: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="deterministic",
        server_default=text("'deterministic'"),
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", server_default=text("'pending'")
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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


class IndoorActionEvent(Base):
    """Completion and rescheduling history for an indoor action."""

    __tablename__ = "indoor_action_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('completed','rescheduled','reopened')",
            name="event_type_allowed",
        ),
        CheckConstraint("note IS NULL OR char_length(note) <= 300", name="note_length"),
        CheckConstraint(
            "new_due_at IS NULL OR previous_due_at IS NULL OR new_due_at <> previous_due_at",
            name="due_change",
        ),
        Index(
            "ix_indoor_action_events_recommendation", "recommendation_id", "created_at"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    recommendation_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "indoor_recommendations.id",
            name="fk_indoor_action_events_recommendation",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    household_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(16), nullable=False)
    previous_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    new_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
