"""align ecoroute constraint names with ORM metadata

Revision ID: 0009_constraint_names
Revises: 0008_ecoroute_impact
Create Date: 2026-11-21 00:00:00.000000

Revision 0008 created the ecoroute and goal check constraints with names that
omitted the ORM prefix, so a migrated database did not match the metadata.
Renaming them here (instead of editing 0008) keeps already-migrated databases
on the same forward path.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0009_constraint_names"
down_revision: str | None = "0008_ecoroute_impact"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RENAMES: tuple[tuple[str, str, str], ...] = (
    (
        "saved_journeys",
        "ck_saved_journeys_distance_non_negative",
        "ck_saved_journeys_journey_distance_non_negative",
    ),
    (
        "saved_journeys",
        "ck_saved_journeys_duration_non_negative",
        "ck_saved_journeys_journey_duration_non_negative",
    ),
    (
        "saved_journeys",
        "ck_saved_journeys_passengers_positive",
        "ck_saved_journeys_journey_passengers_positive",
    ),
    (
        "emission_calculations",
        "ck_emission_calculations_quantity_non_negative",
        "ck_emission_calculations_calculation_quantity_non_negative",
    ),
    (
        "emission_calculations",
        "ck_emission_calculations_result_non_negative",
        "ck_emission_calculations_calculation_result_non_negative",
    ),
    (
        "emission_calculations",
        "ck_emission_calculations_factor_non_negative",
        "ck_emission_calculations_calculation_factor_non_negative",
    ),
    (
        "sustainability_goals",
        "ck_sustainability_goals_target_positive",
        "ck_sustainability_goals_goal_target_positive",
    ),
    (
        "sustainability_goals",
        "ck_sustainability_goals_current_non_negative",
        "ck_sustainability_goals_goal_current_non_negative",
    ),
)


def upgrade() -> None:
    for table, old_name, new_name in _RENAMES:
        op.execute(
            f'ALTER TABLE "{table}" RENAME CONSTRAINT "{old_name}" TO "{new_name}"'
        )


def downgrade() -> None:
    for table, old_name, new_name in reversed(_RENAMES):
        op.execute(
            f'ALTER TABLE "{table}" RENAME CONSTRAINT "{new_name}" TO "{old_name}"'
        )
