"""ecoroute journeys, emission calculations and sustainability goals

Revision ID: 0008_ecoroute_impact
Revises: 0007_indoor_shield
Create Date: 2026-11-21 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_ecoroute_impact"
down_revision: str | None = "0007_indoor_shield"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ACCESSIBILITY_NEEDS = (
    "'wheelchair','step-free','priority-seating','audio-announcements','none'"
)
_TRAVEL_MODES = (
    "'walk','cycle','two-wheeler','car','bus','train','metro','shared-mobility'"
)
_ACTIVITY_TYPES = (
    "'walked','public-transport','worked-from-home','planted-tree'"
)
_GOAL_UNITS = "'km','days','trees'"


def upgrade() -> None:
    op.create_table(
        "saved_journeys",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("household_id", sa.Uuid(), nullable=False),
        sa.Column("origin_lat", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("origin_lon", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("destination_lat", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("destination_lon", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("travel_date", sa.Date(), nullable=True),
        sa.Column(
            "modes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("selected_mode", sa.String(length=32), nullable=False),
        sa.Column(
            "passengers", sa.Integer(), nullable=False, server_default=sa.text("1")
        ),
        sa.Column("distance_km", sa.Numeric(precision=8, scale=3), nullable=False),
        sa.Column(
            "duration_min", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("co2e_kg", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column(
            "co2e_per_passenger_kg",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
        ),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "distance_km >= 0",
            name=op.f("ck_saved_journeys_distance_non_negative"),
        ),
        sa.CheckConstraint(
            "duration_min >= 0",
            name=op.f("ck_saved_journeys_duration_non_negative"),
        ),
        sa.CheckConstraint(
            "passengers >= 1",
            name=op.f("ck_saved_journeys_passengers_positive"),
        ),
        sa.CheckConstraint(
            f"selected_mode IN ({_TRAVEL_MODES})",
            name=op.f("ck_saved_journeys_selected_mode_allowed"),
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["households.id"],
            name=op.f("fk_saved_journeys_household_id_households"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_saved_journeys")),
    )
    op.create_index(
        "ix_saved_journeys_household_created",
        "saved_journeys",
        ["household_id", "created_at"],
    )

    op.create_table(
        "emission_calculations",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("household_id", sa.Uuid(), nullable=False),
        sa.Column("activity_type", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("result_kg_co2e", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("factor_key", sa.String(length=64), nullable=False),
        sa.Column("factor_value", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column("factor_unit", sa.String(length=32), nullable=False),
        sa.Column("factor_version", sa.String(length=32), nullable=False),
        sa.Column(
            "factor_source_url", sa.String(length=500), nullable=False
        ),
        sa.Column("calculation_method", sa.String(length=200), nullable=False),
        sa.Column(
            "assumptions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "quantity >= 0",
            name=op.f("ck_emission_calculations_quantity_non_negative"),
        ),
        sa.CheckConstraint(
            "result_kg_co2e >= 0",
            name=op.f("ck_emission_calculations_result_non_negative"),
        ),
        sa.CheckConstraint(
            "factor_value >= 0",
            name=op.f("ck_emission_calculations_factor_non_negative"),
        ),
        sa.CheckConstraint(
            f"activity_type IN ({_ACTIVITY_TYPES})",
            name=op.f("ck_emission_calculations_activity_type_allowed"),
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["households.id"],
            name=op.f("fk_emission_calculations_household_id_households"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_emission_calculations")),
    )
    op.create_index(
        "ix_calculations_household_created",
        "emission_calculations",
        ["household_id", "created_at"],
    )
    op.create_index(
        "ix_calculations_activity_type",
        "emission_calculations",
        ["household_id", "activity_type"],
    )

    op.create_table(
        "sustainability_goals",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("household_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("activity_type", sa.String(length=64), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("target_value", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column(
            "current_value",
            sa.Numeric(precision=10, scale=3),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
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
            "target_value > 0",
            name=op.f("ck_sustainability_goals_target_positive"),
        ),
        sa.CheckConstraint(
            "current_value >= 0",
            name=op.f("ck_sustainability_goals_current_non_negative"),
        ),
        sa.CheckConstraint(
            f"activity_type IN ({_ACTIVITY_TYPES})",
            name=op.f("ck_sustainability_goals_activity_type_allowed"),
        ),
        sa.CheckConstraint(
            f"unit IN ({_GOAL_UNITS})",
            name=op.f("ck_sustainability_goals_unit_allowed"),
        ),
        sa.CheckConstraint(
            "btrim(title) <> ''",
            name=op.f("ck_sustainability_goals_title_present"),
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["households.id"],
            name=op.f("fk_sustainability_goals_household_id_households"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sustainability_goals")),
    )
    op.create_index(
        "ix_goals_household_active",
        "sustainability_goals",
        ["household_id", "is_active"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_goals_household_active", table_name="sustainability_goals"
    )
    op.drop_table("sustainability_goals")
    op.drop_index(
        "ix_calculations_activity_type", table_name="emission_calculations"
    )
    op.drop_index(
        "ix_calculations_household_created", table_name="emission_calculations"
    )
    op.drop_table("emission_calculations")
    op.drop_index(
        "ix_saved_journeys_household_created", table_name="saved_journeys"
    )
    op.drop_table("saved_journeys")