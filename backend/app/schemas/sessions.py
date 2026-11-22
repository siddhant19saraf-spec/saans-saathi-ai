"""Anonymous session contracts."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consent_version: str = Field(min_length=1, max_length=32)
    health_consent: bool = False


class SessionCreated(BaseModel):
    token: str
    expires_at: datetime
    profile_id: UUID


class ConsentState(BaseModel):
    version: str
    health_consent_at: datetime | None


class HealthConsentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    health_consent: bool


class SessionInfo(BaseModel):
    profile_id: UUID
    has_household: bool
    consent: ConsentState
    expires_at: datetime
