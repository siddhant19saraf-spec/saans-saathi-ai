"""Eco-route comparison contracts (pinned to the frontend Zod schema)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TravelMode = Literal[
    "walk", "cycle", "two-wheeler", "car", "bus", "train", "metro", "shared-mobility"
]

AccessibilityNeed = Literal[
    "wheelchair", "step-free", "priority-seating", "audio-announcements", "none"
]


class Point(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class EcoRouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin: Point
    destination: Point
    modes: list[TravelMode] = Field(min_length=1, max_length=8)
    depart_at: datetime | None = None
    travel_date: date | None = None
    passengers: int = Field(default=1, ge=1, le=8)
    accessibility_needs: list[AccessibilityNeed] = Field(default_factory=list)
    max_duration_min: int | None = Field(default=None, ge=1, le=1440)

    @field_validator("modes")
    @classmethod
    def _unique_modes(cls, value: list[TravelMode]) -> list[TravelMode]:
        if len(value) != len(set(value)):
            raise ValueError("modes must not contain duplicates.")
        return value

    @field_validator("accessibility_needs")
    @classmethod
    def _unique_accessibility(
        cls, value: list[AccessibilityNeed]
    ) -> list[AccessibilityNeed]:
        if len(value) != len(set(value)):
            raise ValueError("accessibility_needs must not contain duplicates.")
        return value

    @field_validator("travel_date")
    @classmethod
    def _travel_date_not_in_past(cls, value: date | None) -> date | None:
        if value is not None and value < date.today():
            raise ValueError("travel_date must not be in the past.")
        return value


class RouteSummary(BaseModel):
    distance_km: float
    duration_min: int
    source: str
    is_estimate: bool


class ModeComparison(BaseModel):
    mode: str
    co2e_kg: float | None
    co2e_per_passenger_kg: float | None
    exposure_index: int | None
    duration_min: int | None
    recommended_for: list[str]
    accessible: bool


class Assumption(BaseModel):
    key: str
    value: float | str
    source: str


class EcoRouteComparison(BaseModel):
    route: RouteSummary
    modes: list[ModeComparison]
    tradeoff_note: str | None
    assumptions: list[Assumption]


class JourneySave(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin: Point
    destination: Point
    travel_date: date | None = None
    modes: list[TravelMode] = Field(min_length=1, max_length=8)
    selected_mode: TravelMode
    passengers: int = Field(default=1, ge=1, le=8)
    distance_km: float = Field(ge=0)
    duration_min: int = Field(ge=0)
    co2e_kg: float | None = None
    co2e_per_passenger_kg: float | None = None
    notes: str | None = Field(default=None, max_length=500)


class JourneyOut(JourneySave):
    id: str
    created_at: datetime


class ProviderHealth(BaseModel):
    name: str
    healthy: bool
    kind: str
    note: str | None = None


__all__ = [
    "AccessibilityNeed",
    "Assumption",
    "EcoRouteComparison",
    "EcoRouteRequest",
    "JourneyOut",
    "JourneySave",
    "ModeComparison",
    "Point",
    "ProviderHealth",
    "RouteSummary",
    "TravelMode",
]
