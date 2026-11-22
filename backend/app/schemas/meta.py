"""Operational metadata contract."""

from __future__ import annotations

from pydantic import BaseModel


class ProviderMeta(BaseModel):
    name: str
    configured: bool
    circuit_state: str | None = None


class Meta(BaseModel):
    service: str
    version: str
    environment: str
    ai_configured: bool
    ai_model: str
    air_provider: ProviderMeta
    limits: dict[str, int]
