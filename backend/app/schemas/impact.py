"""Sustainability ledger and factor-registry contracts."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ActivityType = Literal["walked", "public-transport", "worked-from-home", "planted-tree"]

_UNITS: dict[str, str] = {
    "walked": "km",
    "public-transport": "km",
    "worked-from-home": "days",
    "planted-tree": "trees",
}


class ActivityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activity_type: ActivityType
    quantity: float = Field(gt=0, le=100_000)
    unit: str | None = Field(default=None, max_length=16)
    occurred_on: date


class Activity(BaseModel):
    id: UUID
    activity_type: str
    occurred_on: date
    quantity: float
    unit: str
    co2e_kg: float
    factor_key: str
    factor_value: float
    factor_unit: str
    factor_version: str
    factor_source_url: str
    created_at: datetime


class TypeBreakdown(BaseModel):
    activity_type: str
    co2e_kg: float
    count: int


class ImpactSummary(BaseModel):
    range: str
    total_co2e_kg: float
    activity_count: int
    by_type: list[TypeBreakdown]


class FactorOut(BaseModel):
    key: str
    label: str
    value: float
    unit: str
    source: str
    source_url: str
    version: str
    retrieved_at: date


class GoalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    activity_type: ActivityType
    unit: str
    target_value: float = Field(gt=0, le=1_000_000)
    target_date: date | None = None


class GoalUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    target_value: float | None = Field(default=None, gt=0, le=1_000_000)
    target_date: date | None = None
    is_active: bool | None = None


class GoalOut(BaseModel):
    id: UUID
    title: str
    description: str | None
    activity_type: str
    unit: str
    target_value: float
    current_value: float
    target_date: date | None
    is_active: bool
    progress_percent: float | None
    is_complete: bool
    created_at: datetime
    updated_at: datetime


class BaselineSavings(BaseModel):
    """Estimated emissions avoided against a documented baseline.

    ``baseline_co2e_kg`` is the modelled baseline (never a measured value).
    ``activity_co2e_kg`` is the logged activity emissions.
    ``savings_co2e_kg`` is baseline minus activity, only when baseline exists.
    """

    baseline_co2e_kg: float | None
    baseline_basis: str | None
    activity_co2e_kg: float
    savings_co2e_kg: float | None
    savings_basis: str | None


class TrendPoint(BaseModel):
    period: str  # ISO week or month label
    co2e_kg: float
    activity_count: int


class ImpactTrends(BaseModel):
    weekly: list[TrendPoint]
    monthly: list[TrendPoint]


class MethodologyOut(BaseModel):
    formula: str
    factors_used: list[str]
    assumptions: list[str]
    limitations: list[str]


def unit_for(activity_type: str) -> str:
    return _UNITS[activity_type]


__all__ = [
    "Activity",
    "ActivityCreate",
    "ActivityType",
    "BaselineSavings",
    "FactorOut",
    "GoalCreate",
    "GoalOut",
    "GoalUpdate",
    "ImpactSummary",
    "ImpactTrends",
    "MethodologyOut",
    "TrendPoint",
    "TypeBreakdown",
    "unit_for",
]
