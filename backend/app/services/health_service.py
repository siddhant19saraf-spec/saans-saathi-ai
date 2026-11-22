"""Health aggregation.

A missing database in development is reported as ``degraded`` rather than
``ok``. A configured but unreachable database is reported as ``unhealthy`` and
the endpoint returns 503, so a platform health check cannot route traffic to a
process that cannot serve data.
"""

from __future__ import annotations

from typing import Literal

from app.core.config import Settings
from app.core.database import Database
from app.schemas.health import ComponentState, HealthChecks, HealthResponse
from app.utils.time import utc_now


class HealthService:
    def __init__(self, settings: Settings, database: Database) -> None:
        self._settings = settings
        self._database = database

    async def check(self) -> HealthResponse:
        database_state = await self._database_state()
        status: Literal["ok", "degraded", "unhealthy"]
        if database_state is ComponentState.UNAVAILABLE:
            status = "unhealthy"
        elif database_state is ComponentState.NOT_CONFIGURED:
            status = "degraded"
        else:
            status = "ok"

        return HealthResponse(
            status=status,
            service=self._settings.app_name,
            version=self._settings.app_version,
            environment=self._settings.app_env,
            timestamp=utc_now(),
            checks=HealthChecks(
                database=database_state,
                ai_provider=(
                    ComponentState.CONFIGURED
                    if self._settings.ai_configured
                    else ComponentState.NOT_CONFIGURED
                ),
                air_quality_provider=ComponentState.CONFIGURED,
            ),
        )

    async def _database_state(self) -> ComponentState:
        if not self._database.is_configured:
            return ComponentState.NOT_CONFIGURED
        if await self._database.check():
            return ComponentState.OK
        return ComponentState.UNAVAILABLE
