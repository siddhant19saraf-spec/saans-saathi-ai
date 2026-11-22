from __future__ import annotations

import os

import pytest

from app.core.config import Settings
from app.core.database import Database


async def test_unconfigured_database_is_not_ok() -> None:
    database = Database(Settings(_env_file=None, database_url=None))

    assert database.is_configured is False
    assert database.engine is None
    assert await database.check() is False


async def test_session_is_rejected_when_not_configured() -> None:
    database = Database(Settings(_env_file=None, database_url=None))

    with pytest.raises(RuntimeError, match="not configured"):
        async with database.session():
            pass


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not set; live PostgreSQL check skipped.",
)
async def test_live_database_check() -> None:
    database = Database(
        Settings(_env_file=None, database_url=os.environ["TEST_DATABASE_URL"])
    )
    try:
        assert await database.check() is True
    finally:
        await database.dispose()
