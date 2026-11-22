"""Prove the Alembic chain runs on a disposable database.

The test creates a uniquely named database on the same server as
TEST_DATABASE_URL, runs the real migration command, checks for model drift,
downgrades to base and drops the database. It never touches the database named
in TEST_DATABASE_URL.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import uuid
from collections.abc import Sequence
from pathlib import Path

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.models import Base

_BACKEND = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not set; migration execution test skipped.",
)

_APP_TABLES = {
    "ai_conversations",
    "ai_messages",
    "air_quality_fetch_log",
    "air_quality_forecasts",
    "air_quality_snapshots",
    "emission_calculations",
    "household_members",
    "household_preferences",
    "households",
    "indoor_action_events",
    "indoor_assessments",
    "indoor_recommendations",
    "indoor_rooms",
    "indoor_sensor_readings",
    "indoor_sensors",
    "indoor_sources",
    "privacy_events",
    "profiles",
    "recommendations",
    "routine_activities",
    "routine_items",
    "routines",
    "saved_journeys",
    "saved_locations",
    "sustainability_activities",
    "sustainability_goals",
    "usage_daily",
}


def _alembic(
    database_url: str, args: Sequence[str]
) -> subprocess.CompletedProcess[str]:
    environment = {**os.environ, "DATABASE_URL": database_url}
    return subprocess.run(  # noqa: S603 - fixed executable, no shell
        [sys.executable, "-m", "alembic", *args],
        cwd=_BACKEND,
        env=environment,
        capture_output=True,
        text=True,
        timeout=180,
    )


async def _public_tables(database_url: str) -> set[str]:
    engine = create_async_engine(database_url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            rows = await connection.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            return set(rows.scalars().all())
    finally:
        await engine.dispose()


def _expected_constraints(
    kind: type[CheckConstraint | ForeignKeyConstraint],
) -> set[tuple[str, str]]:
    expected: set[tuple[str, str]] = set()
    for table in Base.metadata.tables.values():
        for constraint in table.constraints:
            if isinstance(constraint, kind) and constraint.name is not None:
                expected.add((table.name, str(constraint.name)))
    return expected


async def _database_constraints(database_url: str) -> set[tuple[str, str]]:
    engine = create_async_engine(database_url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            rows = await connection.execute(
                text(
                    "SELECT conrelid::regclass::text, conname "
                    "FROM pg_constraint "
                    "WHERE connamespace = 'public'::regnamespace "
                    "AND contype IN ('c','f')"
                )
            )
            return {(table_name, name) for table_name, name in rows.all()}
    finally:
        await engine.dispose()


async def _revision(database_url: str) -> str | None:
    engine = create_async_engine(database_url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            return await connection.scalar(
                text("SELECT version_num FROM alembic_version")
            )
    finally:
        await engine.dispose()


async def _create_database(admin_url: str, name: str) -> None:
    engine = create_async_engine(
        admin_url, isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    try:
        async with engine.connect() as connection:
            await connection.execute(text(f'CREATE DATABASE "{name}"'))
    finally:
        await engine.dispose()


async def _drop_database(admin_url: str, name: str) -> None:
    engine = create_async_engine(
        admin_url, isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    try:
        async with engine.connect() as connection:
            await connection.execute(
                text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
            )
    finally:
        await engine.dispose()


async def test_windows_async_url_is_used_directly() -> None:
    # Guard against accidentally passing a synchronous PostgreSQL URL to the
    # async migration runner; the project standard is psycopg 3 async.
    url = make_url(os.environ["TEST_DATABASE_URL"])
    assert url.drivername == "postgresql+psycopg"


async def test_migration_chain_upgrades_checks_and_downgrades() -> None:
    base_url = make_url(os.environ["TEST_DATABASE_URL"])
    database_name = f"saans_migration_{uuid.uuid4().hex[:10]}"
    admin_url = base_url.set(database="postgres").render_as_string(hide_password=False)
    temporary_url = base_url.set(database=database_name).render_as_string(
        hide_password=False
    )

    await _create_database(admin_url, database_name)
    try:
        upgrade = await asyncio.to_thread(_alembic, temporary_url, ("upgrade", "head"))
        assert upgrade.returncode == 0, upgrade.stderr[-3000:]

        tables = await _public_tables(temporary_url)
        assert tables == _APP_TABLES | {"alembic_version"}
        assert await _revision(temporary_url) == "0009_constraint_names"

        migrated_constraints = await _database_constraints(temporary_url)
        assert _expected_constraints(CheckConstraint) <= migrated_constraints
        assert _expected_constraints(ForeignKeyConstraint) <= migrated_constraints

        drift = await asyncio.to_thread(_alembic, temporary_url, ("check",))
        assert drift.returncode == 0, drift.stdout[-3000:] + drift.stderr[-3000:]

        downgrade = await asyncio.to_thread(
            _alembic, temporary_url, ("downgrade", "base")
        )
        assert downgrade.returncode == 0, downgrade.stderr[-3000:]

        remaining = await _public_tables(temporary_url)
        assert remaining == {"alembic_version"}
        assert await _revision(temporary_url) is None
    finally:
        await _drop_database(admin_url, database_name)
