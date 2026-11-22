"""versioned smart routines, activity preferences and scheduled items

Adds schedule versions to ``routines`` so manual overrides and replans can be
inspected without losing older plans, a household-level activity preference
table for the planner, and a normalised snapshot of the activities assigned to
each plan. JSON plan documents remain the API representation; the new rows make
updates and history queries explicit.

Revision ID: 0006_smart_routine
Revises: 0005_family_intelligence
Create Date: 2026-11-19 21:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_smart_routine"
down_revision: str | None = "0005_family_intelligence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CATEGORIES = (
    "'morning_walk','outdoor_sports','school_travel','college_travel',"
    "'office_commute','grocery_shopping','outdoor_recreation','indoor_exercise',"
    "'household_activity','gardening','other'"
)


def upgrade() -> None:
    op.add_column(
        "routines",
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )
    op.add_column(
        "routines",
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
    )
    # Plans stored before the versioned planner are not readable by the new
    # engine. Keep their history but do not serve them as the active schedule.
    op.execute("UPDATE routines SET status = 'superseded'")
    op.add_column(
        "routines",
        sa.Column("parent_routine_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "routines",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_foreign_key(
        op.f("fk_routines_parent_routine_id_routines"),
        "routines",
        "routines",
        ["parent_routine_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        op.f("ck_routines_version_positive"), "routines", "version >= 1"
    )
    op.create_check_constraint(
        op.f("ck_routines_status_allowed"),
        "routines",
        "status IN ('active','superseded')",
    )
    op.drop_constraint("uq_routines_identity", "routines", type_="unique")
    op.create_unique_constraint(
        "uq_routines_identity",
        "routines",
        ["household_id", "plan_date", "inputs_hash", "version"],
    )
    op.create_index(
        "ix_routines_household_status", "routines", ["household_id", "status"]
    )

    op.create_table(
        "routine_activities",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("household_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=80), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=False),
        sa.Column("preferred_start", sa.String(length=5), nullable=False),
        sa.Column("earliest_start", sa.String(length=5), nullable=True),
        sa.Column("latest_start", sa.String(length=5), nullable=True),
        sa.Column("venue", sa.String(length=16), nullable=False),
        sa.Column(
            "fixed", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "priority",
            sa.String(length=8),
            nullable=False,
            server_default=sa.text("'medium'"),
        ),
        sa.Column(
            "intensity",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'moderate'"),
        ),
        sa.Column(
            "member_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "location",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("indoor_alternative", sa.String(length=80), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column(
            "active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
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
            "btrim(title) <> ''", name=op.f("ck_routine_activities_title_present")
        ),
        sa.CheckConstraint(
            f"category IN ({_CATEGORIES})",
            name=op.f("ck_routine_activities_category_allowed"),
        ),
        sa.CheckConstraint(
            "duration_min BETWEEN 15 AND 240",
            name=op.f("ck_routine_activities_duration_range"),
        ),
        sa.CheckConstraint(
            "preferred_start ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'",
            name=op.f("ck_routine_activities_preferred_start_format"),
        ),
        sa.CheckConstraint(
            "earliest_start IS NULL OR earliest_start"
            " ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'",
            name=op.f("ck_routine_activities_earliest_start_format"),
        ),
        sa.CheckConstraint(
            "latest_start IS NULL OR latest_start"
            " ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'",
            name=op.f("ck_routine_activities_latest_start_format"),
        ),
        sa.CheckConstraint(
            "venue IN ('indoor','outdoor')",
            name=op.f("ck_routine_activities_venue_allowed"),
        ),
        sa.CheckConstraint(
            "priority IN ('low','medium','high')",
            name=op.f("ck_routine_activities_priority_allowed"),
        ),
        sa.CheckConstraint(
            "intensity IN ('light','moderate','vigorous')",
            name=op.f("ck_routine_activities_intensity_allowed"),
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["households.id"],
            name=op.f("fk_routine_activities_household_id_households"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_routine_activities")),
    )
    op.create_index(
        "ix_routine_activities_household",
        "routine_activities",
        ["household_id", "active"],
    )

    op.create_table(
        "routine_items",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("routine_id", sa.Uuid(), nullable=False),
        sa.Column("activity_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=80), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("venue", sa.String(length=16), nullable=False),
        sa.Column("priority", sa.String(length=8), nullable=False),
        sa.Column(
            "fixed", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_min", sa.Integer(), nullable=True),
        sa.Column(
            "override", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "rationale",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "context",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "alternatives",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
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
            "status IN ('scheduled','unscheduled','cancelled','done','skipped')",
            name=op.f("ck_routine_items_status_allowed"),
        ),
        sa.CheckConstraint(
            "start_at IS NULL OR end_at IS NULL OR end_at > start_at",
            name=op.f("ck_routine_items_end_after_start"),
        ),
        sa.ForeignKeyConstraint(
            ["routine_id"],
            ["routines.id"],
            name=op.f("fk_routine_items_routine_id_routines"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_routine_items")),
        sa.UniqueConstraint(
            "routine_id", "activity_id", name="uq_routine_items_activity"
        ),
    )
    op.create_index("ix_routine_items_routine", "routine_items", ["routine_id"])


def downgrade() -> None:
    op.drop_index("ix_routine_items_routine", table_name="routine_items")
    op.drop_table("routine_items")
    op.drop_index("ix_routine_activities_household", table_name="routine_activities")
    op.drop_table("routine_activities")

    op.drop_index("ix_routines_household_status", table_name="routines")
    op.drop_constraint("uq_routines_identity", "routines", type_="unique")
    op.drop_constraint(op.f("ck_routines_status_allowed"), "routines", type_="check")
    op.drop_constraint(op.f("ck_routines_version_positive"), "routines", type_="check")
    op.drop_constraint(
        op.f("fk_routines_parent_routine_id_routines"), "routines", type_="foreignkey"
    )
    # The old uniqueness rule cannot represent multiple versions; keep the most
    # recent row per identity before restoring it.
    op.execute(
        "DELETE FROM routines a USING routines b "
        "WHERE a.household_id = b.household_id "
        "AND a.plan_date = b.plan_date "
        "AND a.inputs_hash = b.inputs_hash "
        "AND a.generated_at < b.generated_at"
    )
    op.create_unique_constraint(
        "uq_routines_identity",
        "routines",
        ["household_id", "plan_date", "inputs_hash"],
    )
    op.drop_column("routines", "updated_at")
    op.drop_column("routines", "parent_routine_id")
    op.drop_column("routines", "status")
    op.drop_column("routines", "version")
