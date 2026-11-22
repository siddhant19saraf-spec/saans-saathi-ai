"""family profile, preference and recommendation fields

Adds a household display name, transport and notification preferences, and a
structured JSON payload plus rule id on generated recommendations. The payload
lets the deterministic family engine round-trip the exact context it used
without inventing columns for every optional field.

Revision ID: 0005_family_intelligence
Revises: 0004_air_source_types
Create Date: 2026-11-19 18:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_family_intelligence"
down_revision: str | None = "0004_air_source_types"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "households",
        sa.Column(
            "name",
            sa.String(length=80),
            nullable=False,
            server_default="Household",
        ),
    )
    op.create_check_constraint(
        op.f("ck_households_name_present"),
        "households",
        "btrim(name) <> ''",
    )

    op.add_column(
        "household_preferences",
        sa.Column(
            "transport_mode",
            sa.String(length=16),
            nullable=False,
            server_default="mixed",
        ),
    )
    op.add_column(
        "household_preferences",
        sa.Column(
            "notifications_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "household_preferences",
        sa.Column(
            "notify_alerts",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "household_preferences",
        sa.Column(
            "notify_daily_summary",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "household_preferences",
        sa.Column("quiet_hours_start", sa.String(length=5), nullable=True),
    )
    op.add_column(
        "household_preferences",
        sa.Column("quiet_hours_end", sa.String(length=5), nullable=True),
    )
    op.create_check_constraint(
        op.f("ck_household_preferences_transport_mode_allowed"),
        "household_preferences",
        "transport_mode IN ('walk','cycle','public','private','mixed')",
    )
    op.create_check_constraint(
        op.f("ck_household_preferences_quiet_hours_start_format"),
        "household_preferences",
        "quiet_hours_start IS NULL OR quiet_hours_start"
        " ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'",
    )
    op.create_check_constraint(
        op.f("ck_household_preferences_quiet_hours_end_format"),
        "household_preferences",
        "quiet_hours_end IS NULL OR quiet_hours_end"
        " ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'",
    )

    op.add_column(
        "recommendations",
        sa.Column("rule_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "recommendations",
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.create_check_constraint(
        op.f("ck_recommendations_rule_id_present"),
        "recommendations",
        "rule_id IS NULL OR btrim(rule_id) <> ''",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_recommendations_rule_id_present"),
        "recommendations",
        type_="check",
    )
    op.drop_column("recommendations", "payload")
    op.drop_column("recommendations", "rule_id")

    for name in (
        "ck_household_preferences_quiet_hours_end_format",
        "ck_household_preferences_quiet_hours_start_format",
        "ck_household_preferences_transport_mode_allowed",
    ):
        op.drop_constraint(op.f(name), "household_preferences", type_="check")
    op.drop_column("household_preferences", "quiet_hours_end")
    op.drop_column("household_preferences", "quiet_hours_start")
    op.drop_column("household_preferences", "notify_daily_summary")
    op.drop_column("household_preferences", "notify_alerts")
    op.drop_column("household_preferences", "notifications_enabled")
    op.drop_column("household_preferences", "transport_mode")

    op.drop_constraint(
        op.f("ck_households_name_present"), "households", type_="check"
    )
    op.drop_column("households", "name")
