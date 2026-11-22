"""air-quality source types and expanded provider failure vocabulary

Adds an explicit ``source_type`` to cached snapshots so a model grid forecast
can never be presented as a ground-station observation, records the station
name alongside the station id, and allows the new provider failure statuses in
the fetch audit log. Existing migration history is untouched.

Revision ID: 0004_air_source_types
Revises: 0003_integrity_constraints
Create Date: 2026-11-19 16:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_air_source_types"
down_revision: str | None = "0003_integrity_constraints"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OLD_STATUSES = (
    "status IN ('ok','timeout','http_error','parse_error','circuit_open')"
)
_NEW_STATUSES = (
    "status IN ('ok','timeout','http_error','parse_error','circuit_open',"
    "'rate_limited','unauthorized','not_configured','not_found','unsupported')"
)


def upgrade() -> None:
    op.add_column(
        "air_quality_snapshots",
        sa.Column(
            "source_type",
            sa.String(length=24),
            nullable=False,
            server_default="model_forecast",
        ),
    )
    op.add_column(
        "air_quality_snapshots",
        sa.Column("station_name", sa.String(length=160), nullable=True),
    )
    op.execute(
        "UPDATE air_quality_snapshots SET source_type = 'ground_observation' "
        "WHERE kind = 'measured'"
    )
    op.create_check_constraint(
        op.f("ck_air_quality_snapshots_source_type_allowed"),
        "air_quality_snapshots",
        "source_type IN "
        "('ground_observation','model_forecast','historical_observation')",
    )

    op.drop_constraint(
        op.f("ck_air_quality_fetch_log_status_allowed"),
        "air_quality_fetch_log",
        type_="check",
    )
    op.create_check_constraint(
        op.f("ck_air_quality_fetch_log_status_allowed"),
        "air_quality_fetch_log",
        _NEW_STATUSES,
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_air_quality_fetch_log_status_allowed"),
        "air_quality_fetch_log",
        type_="check",
    )
    op.create_check_constraint(
        op.f("ck_air_quality_fetch_log_status_allowed"),
        "air_quality_fetch_log",
        _OLD_STATUSES,
    )

    op.drop_constraint(
        op.f("ck_air_quality_snapshots_source_type_allowed"),
        "air_quality_snapshots",
        type_="check",
    )
    op.drop_column("air_quality_snapshots", "station_name")
    op.drop_column("air_quality_snapshots", "source_type")
