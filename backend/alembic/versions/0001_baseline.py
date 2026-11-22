"""Establish the migration baseline.

No business tables are created in this milestone. The revision exists so the
migration chain, CI check and deployment step are exercised before the approved
schema from docs/BLUEPRINT.md §6 is added.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-11-18
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No schema objects yet."""


def downgrade() -> None:
    """Nothing to revert."""
