"""Emission-factor registry with provenance enforcement."""

from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator

_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "factors" / "registry.json"


class Factor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    label: str
    value: float
    unit: str
    geography: str
    valid_from: date | None = None
    version: str
    source_title: str
    source_url: HttpUrl
    retrieved_on: date
    uncertainty: str
    verified: bool
    derivation: str | None = None

    @field_validator("verified")
    @classmethod
    def _verified_factors_only(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Unverified factors cannot be served by the API.")
        return value


@lru_cache
def load_factors() -> tuple[Factor, ...]:
    payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    factors = tuple(Factor.model_validate(entry) for entry in payload)
    keys = [factor.key for factor in factors]
    if len(keys) != len(set(keys)):
        raise ValueError("Factor registry contains duplicate keys.")
    return factors


def get_factor(key: str) -> Factor:
    for factor in load_factors():
        if factor.key == key:
            return factor
    raise KeyError(f"Unknown emission factor: {key}")
