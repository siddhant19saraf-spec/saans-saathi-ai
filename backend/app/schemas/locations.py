"""Saved-location contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SavedLocationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=60)
    kind: Literal["home", "work", "school", "other"] = "other"
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class SavedLocation(BaseModel):
    id: UUID
    label: str
    kind: str
    lat: float
    lon: float
    created_at: datetime
