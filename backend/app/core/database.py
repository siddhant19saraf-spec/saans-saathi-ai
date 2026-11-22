"""Async PostgreSQL engine ownership and health probing."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Database:
    """Owns the engine and session factory; connects lazily.

    Connecting lazily lets the API start in development without a database and
    lets tests exercise HTTP behaviour without PostgreSQL.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def is_configured(self) -> bool:
        return self._settings.database_url is not None

    @property
    def engine(self) -> AsyncEngine | None:
        url = self._settings.database_url
        if url is None:
            return None
        if self._engine is None:
            self._engine = create_async_engine(
                url,
                pool_pre_ping=True,
                pool_size=self._settings.db_pool_size,
                max_overflow=self._settings.db_max_overflow,
                pool_timeout=self._settings.db_pool_timeout_seconds,
                pool_recycle=1800,
                echo=False,
            )
            self._session_factory = async_sessionmaker(
                self._engine,
                expire_on_commit=False,
                autoflush=False,
            )
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession] | None:
        if self.engine is None:
            return None
        return self._session_factory

    async def check(self) -> bool:
        """Return True when a trivial query succeeds within the timeout.

        Never raises: an unreachable database is a health state, not an
        application crash.
        """
        engine = self.engine
        if engine is None:
            return False
        try:
            async with asyncio.timeout(2.0):
                async with engine.connect() as connection:
                    await connection.execute(text("SELECT 1"))
        except (TimeoutError, SQLAlchemyError, OSError):
            logger.warning("database_unreachable")
            return False
        return True

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
        self._engine = None
        self._session_factory = None

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        factory = self.session_factory
        if factory is None:
            raise RuntimeError("Database is not configured.")
        async with factory() as session:
            yield session
