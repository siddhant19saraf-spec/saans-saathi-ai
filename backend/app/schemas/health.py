"""Health response contract.

The payload intentionally exposes readiness only: no connection strings,
hostnames, versions of internal libraries, or error text from the database.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class ComponentState(StrEnum):
    OK = "ok"
    UNAVAILABLE = "unavailable"
    CONFIGURED = "configured"
    NOT_CONFIGURED = "not_configured"


class HealthChecks(BaseModel):
    database: ComponentState
    ai_provider: ComponentState
    air_quality_provider: ComponentState


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "unhealthy"]
    service: str
    version: str
    environment: str
    timestamp: datetime
    checks: HealthChecks = Field(description="Per-component readiness")
