"""indoor shield assessments, sensors, readings, recommendations and history

Revision ID: 0007_indoor_shield
Revises: 0006_smart_routine
Create Date: 2026-11-20 10:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_indoor_shield"
down_revision: str | None = "0006_smart_routine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

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


def upgrade() -> None:
    op.create_table(
        "indoor_assessments",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("household_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'completed'"),
        ),
        sa.Column("dwelling", sa.String(length=24), nullable=False),
        sa.Column("cooking_fuel", sa.String(length=16), nullable=False),
        sa.Column("cooking_location", sa.String(length=24), nullable=False),
        sa.Column(
            "cooking_exhaust",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("cleaning_frequency", sa.String(length=16), nullable=False),
        sa.Column(
            "sensor_available",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("engine_version", sa.String(length=32), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("confidence", sa.String(length=16), nullable=True),
        sa.Column(
            "assumptions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "limitations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "outdoor_context",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "explanation",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "status IN ('draft','completed')",
            name=op.f("ck_indoor_assessments_status_allowed"),
        ),
        sa.CheckConstraint(
            "dwelling IN ('apartment_ground','apartment_upper','independent','other')",
            name=op.f("ck_indoor_assessments_dwelling_allowed"),
        ),
        sa.CheckConstraint(
            "cooking_fuel IN ('lpg','png','induction','biomass','mixed','other')",
            name=op.f("ck_indoor_assessments_cooking_fuel_allowed"),
        ),
        sa.CheckConstraint(
            "cooking_location IN ('indoor_kitchen','separate_room','outdoor','other')",
            name=op.f("ck_indoor_assessments_cooking_location_allowed"),
        ),
        sa.CheckConstraint(
            "cleaning_frequency IN ('daily','weekly','monthly','less')",
            name=op.f("ck_indoor_assessments_cleaning_frequency_allowed"),
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR confidence IN ('high','medium','low')",
            name=op.f("ck_indoor_assessments_confidence_allowed"),
        ),
        sa.CheckConstraint(
            "engine_version IS NULL OR btrim(engine_version) <> ''",
            name=op.f("ck_indoor_assessments_engine_version_present"),
        ),
        sa.CheckConstraint(
            "notes IS NULL OR char_length(notes) <= 500",
            name=op.f("ck_indoor_assessments_notes_length"),
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["households.id"],
            name=op.f("fk_indoor_assessments_household_id_households"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_indoor_assessments")),
    )
    op.create_index(
        "ix_indoor_assessments_household",
        "indoor_assessments",
        ["household_id", "created_at"],
    )

    op.create_table(
        "indoor_rooms",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("room_type", sa.String(length=24), nullable=False),
        sa.Column("area_m2", sa.Numeric(precision=6, scale=1), nullable=False),
        sa.Column("ceiling_m", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("ventilation", sa.String(length=16), nullable=False),
        sa.Column(
            "windows_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "has_purifier",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("purifier_cadr", sa.Integer(), nullable=True),
        sa.Column(
            "dampness",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'unknown'"),
        ),
        sa.Column(
            "position", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "btrim(name) <> ''", name=op.f("ck_indoor_rooms_name_present")
        ),
        sa.CheckConstraint(
            f"room_type IN ({_ROOM_TYPES})",
            name=op.f("ck_indoor_rooms_room_type_allowed"),
        ),
        sa.CheckConstraint(
            "area_m2 BETWEEN 3 AND 500", name=op.f("ck_indoor_rooms_area_range")
        ),
        sa.CheckConstraint(
            "ceiling_m BETWEEN 2.0 AND 6.0",
            name=op.f("ck_indoor_rooms_ceiling_range"),
        ),
        sa.CheckConstraint(
            f"ventilation IN ({_VENTILATION})",
            name=op.f("ck_indoor_rooms_ventilation_allowed"),
        ),
        sa.CheckConstraint(
            "windows_count BETWEEN 0 AND 20",
            name=op.f("ck_indoor_rooms_windows_range"),
        ),
        sa.CheckConstraint(
            "purifier_cadr IS NULL OR purifier_cadr BETWEEN 0 AND 1500",
            name=op.f("ck_indoor_rooms_purifier_cadr_range"),
        ),
        sa.CheckConstraint(
            f"dampness IN ({_DAMPNESS})",
            name=op.f("ck_indoor_rooms_dampness_allowed"),
        ),
        sa.CheckConstraint(
            "purifier_cadr IS NULL OR has_purifier",
            name=op.f("ck_indoor_rooms_cadr_requires_purifier"),
        ),
        sa.ForeignKeyConstraint(
            ["assessment_id"],
            ["indoor_assessments.id"],
            name=op.f("fk_indoor_rooms_assessment_id_indoor_assessments"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_indoor_rooms")),
    )
    op.create_index("ix_indoor_rooms_assessment", "indoor_rooms", ["assessment_id"])

    op.create_table(
        "indoor_sources",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column(
            "frequency",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'occasional'"),
        ),
        sa.Column("note", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            f"code IN ({_SOURCE_CODES})", name=op.f("ck_indoor_sources_code_allowed")
        ),
        sa.CheckConstraint(
            f"frequency IN ({_SOURCE_FREQUENCY})",
            name=op.f("ck_indoor_sources_frequency_allowed"),
        ),
        sa.CheckConstraint(
            "note IS NULL OR char_length(note) <= 200",
            name=op.f("ck_indoor_sources_note_length"),
        ),
        sa.ForeignKeyConstraint(
            ["assessment_id"],
            ["indoor_assessments.id"],
            name=op.f("fk_indoor_sources_assessment_id_indoor_assessments"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_indoor_sources")),
        sa.UniqueConstraint("assessment_id", "code", name="uq_indoor_sources_code"),
    )
    op.create_index("ix_indoor_sources_assessment", "indoor_sources", ["assessment_id"])

    op.create_table(
        "indoor_sensors",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("household_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("external_id", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=80), nullable=True),
        sa.Column("room_name", sa.String(length=60), nullable=True),
        sa.Column(
            "calibration_status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'unknown'"),
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "btrim(provider) <> ''", name=op.f("ck_indoor_sensors_provider_present")
        ),
        sa.CheckConstraint(
            "btrim(external_id) <> ''",
            name=op.f("ck_indoor_sensors_external_id_present"),
        ),
        sa.CheckConstraint(
            "btrim(name) <> ''", name=op.f("ck_indoor_sensors_name_present")
        ),
        sa.CheckConstraint(
            "calibration_status IN ('verified','unverified','unknown')",
            name=op.f("ck_indoor_sensors_calibration_allowed"),
        ),
        sa.CheckConstraint(
            "status IN ('active','inactive')",
            name=op.f("ck_indoor_sensors_status_allowed"),
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["households.id"],
            name=op.f("fk_indoor_sensors_household_id_households"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_indoor_sensors")),
        sa.UniqueConstraint(
            "provider", "external_id", name="uq_indoor_sensors_identity"
        ),
    )
    op.create_index(
        "ix_indoor_sensors_household", "indoor_sensors", ["household_id", "status"]
    )

    op.create_table(
        "indoor_sensor_readings",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("sensor_id", sa.Uuid(), nullable=False),
        sa.Column("household_id", sa.Uuid(), nullable=False),
        sa.Column("pollutant", sa.String(length=16), nullable=False),
        sa.Column("value", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("calibration_status", sa.String(length=16), nullable=False),
        sa.Column(
            "quality_status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'valid'"),
        ),
        sa.Column("note", sa.String(length=200), nullable=True),
        sa.CheckConstraint(
            f"pollutant IN ({_POLLUTANTS})",
            name=op.f("ck_indoor_sensor_readings_pollutant_allowed"),
        ),
        sa.CheckConstraint(
            "value >= 0", name=op.f("ck_indoor_sensor_readings_value_non_negative")
        ),
        sa.CheckConstraint(
            "btrim(unit) <> ''",
            name=op.f("ck_indoor_sensor_readings_unit_present"),
        ),
        sa.CheckConstraint(
            "calibration_status IN ('verified','unverified','unknown')",
            name=op.f("ck_indoor_sensor_readings_calibration_allowed"),
        ),
        sa.CheckConstraint(
            "quality_status IN ('valid','suspect')",
            name=op.f("ck_indoor_sensor_readings_quality_allowed"),
        ),
        sa.ForeignKeyConstraint(
            ["sensor_id"],
            ["indoor_sensors.id"],
            name=op.f("fk_indoor_sensor_readings_sensor_id_indoor_sensors"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["households.id"],
            name=op.f("fk_indoor_sensor_readings_household_id_households"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_indoor_sensor_readings")),
        sa.UniqueConstraint(
            "sensor_id",
            "pollutant",
            "measured_at",
            name="uq_indoor_readings_identity",
        ),
    )
    op.create_index(
        "ix_indoor_readings_sensor_pollutant",
        "indoor_sensor_readings",
        ["sensor_id", "pollutant", "measured_at"],
    )
    op.create_index(
        "ix_indoor_readings_household",
        "indoor_sensor_readings",
        ["household_id", "measured_at"],
    )

    op.create_table(
        "indoor_recommendations",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("household_id", sa.Uuid(), nullable=False),
        sa.Column("rule_id", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=24), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("issue", sa.String(length=500), nullable=False),
        sa.Column("action", sa.String(length=1000), nullable=False),
        sa.Column("priority", sa.String(length=8), nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False),
        sa.Column("evidence", sa.String(length=500), nullable=False),
        sa.Column("expected_benefit", sa.String(length=500), nullable=False),
        sa.Column("limitations", sa.String(length=700), nullable=False),
        sa.Column("frequency", sa.String(length=16), nullable=False),
        sa.Column(
            "source",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'deterministic'"),
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "category IN ('cooking','cleaning','dust','ventilation','filtration',"
            "'humidity','outdoor_pollution','general')",
            name=op.f("ck_indoor_recommendations_category_allowed"),
        ),
        sa.CheckConstraint(
            "priority IN ('high','medium','low')",
            name=op.f("ck_indoor_recommendations_priority_allowed"),
        ),
        sa.CheckConstraint(
            "priority_score BETWEEN 0 AND 1000",
            name=op.f("ck_indoor_recommendations_score_range"),
        ),
        sa.CheckConstraint(
            "status IN ('pending','completed','dismissed')",
            name=op.f("ck_indoor_recommendations_status_allowed"),
        ),
        sa.CheckConstraint(
            "source IN ('deterministic','ai')",
            name=op.f("ck_indoor_recommendations_source_allowed"),
        ),
        sa.CheckConstraint(
            "btrim(rule_id) <> ''",
            name=op.f("ck_indoor_recommendations_rule_id_present"),
        ),
        sa.CheckConstraint(
            "frequency IN ('once','daily','weekly','monthly')",
            name=op.f("ck_indoor_recommendations_frequency_allowed"),
        ),
        sa.CheckConstraint(
            "completed_at IS NULL OR status = 'completed'",
            name=op.f("ck_indoor_recommendations_completed_requires_status"),
        ),
        sa.ForeignKeyConstraint(
            ["assessment_id"],
            ["indoor_assessments.id"],
            name=op.f("fk_indoor_recommendations_assessment_id_indoor_assessments"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["households.id"],
            name=op.f("fk_indoor_recommendations_household_id_households"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_indoor_recommendations")),
    )
    op.create_index(
        "ix_indoor_recommendations_assessment",
        "indoor_recommendations",
        ["assessment_id", "status"],
    )
    op.create_index(
        "ix_indoor_recommendations_household",
        "indoor_recommendations",
        ["household_id", "status"],
    )

    op.create_table(
        "indoor_action_events",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("recommendation_id", sa.Uuid(), nullable=False),
        sa.Column("household_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=16), nullable=False),
        sa.Column("previous_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("new_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.String(length=300), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "event_type IN ('completed','rescheduled','reopened')",
            name=op.f("ck_indoor_action_events_event_type_allowed"),
        ),
        sa.CheckConstraint(
            "note IS NULL OR char_length(note) <= 300",
            name=op.f("ck_indoor_action_events_note_length"),
        ),
        sa.CheckConstraint(
            "new_due_at IS NULL OR previous_due_at IS NULL OR new_due_at <> previous_due_at",
            name=op.f("ck_indoor_action_events_due_change"),
        ),
        sa.ForeignKeyConstraint(
            ["recommendation_id"],
            ["indoor_recommendations.id"],
            name="fk_indoor_action_events_recommendation",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["households.id"],
            name=op.f("fk_indoor_action_events_household_id_households"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_indoor_action_events")),
    )
    op.create_index(
        "ix_indoor_action_events_recommendation",
        "indoor_action_events",
        ["recommendation_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_indoor_action_events_recommendation",
        table_name="indoor_action_events",
    )
    op.drop_table("indoor_action_events")
    op.drop_index(
        "ix_indoor_recommendations_household",
        table_name="indoor_recommendations",
    )
    op.drop_index(
        "ix_indoor_recommendations_assessment",
        table_name="indoor_recommendations",
    )
    op.drop_table("indoor_recommendations")
    op.drop_index("ix_indoor_readings_household", table_name="indoor_sensor_readings")
    op.drop_index(
        "ix_indoor_readings_sensor_pollutant", table_name="indoor_sensor_readings"
    )
    op.drop_table("indoor_sensor_readings")
    op.drop_index("ix_indoor_sensors_household", table_name="indoor_sensors")
    op.drop_table("indoor_sensors")
    op.drop_index("ix_indoor_sources_assessment", table_name="indoor_sources")
    op.drop_table("indoor_sources")
    op.drop_index("ix_indoor_rooms_assessment", table_name="indoor_rooms")
    op.drop_table("indoor_rooms")
    op.drop_index("ix_indoor_assessments_household", table_name="indoor_assessments")
    op.drop_table("indoor_assessments")
