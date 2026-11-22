"""Family profile and recommendation contracts.

The profile deliberately carries only age bands, coarse health flags and
activity preferences. No names, contact details or diagnoses are stored.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.family_rules import Action, Confidence, GuidanceBasis
from app.schemas.household import (
    ActivityType,
    FamilyPreferences,
    HouseholdUpsert,
    Member,
    MemberCreate,
)


class FamilyProfileCreate(HouseholdUpsert):
    """Create or replace a family profile.

    ``HouseholdUpsert`` supplies dwelling, cooking fuel, purifier and timezone
    fields used by indoor guidance. The family profile adds a name, required
    coordinates and at least one member.
    """

    name: str = Field(min_length=2, max_length=80)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    members: list[MemberCreate] = Field(min_length=1, max_length=12)


class FamilyProfile(BaseModel):
    id: UUID
    name: str
    size: int
    lat: float | None
    lon: float | None
    city: str | None
    timezone: str
    dwelling: str
    cooking_fuel: str
    has_purifier: bool
    purifier_cadr: int | None
    room_area_m2: int | None
    ceiling_m: float | None
    members: list[Member]
    has_children: bool
    has_older_adults: bool
    has_health_flags: bool
    created_at: datetime
    updated_at: datetime


class PollutionContext(BaseModel):
    provider: str | None
    source_type: (
        Literal[
            "ground_observation",
            "model_forecast",
            "historical_observation",
        ]
        | None
    )
    aqi: int | None
    category: str | None
    pm2_5: float | None
    pm10: float | None
    observed_at: datetime | None
    fetched_at: datetime | None
    age_minutes: int | None
    stale: bool
    forecast_used: bool
    forecast_only: bool
    guidance_basis: GuidanceBasis
    guidance_basis_label: str
    aqi_unavailable_reason: str | None = None
    attribution: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    source: str
    note: str


class FamilyRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation_id: UUID
    activity: ActivityType
    activity_title: str
    recommended_action: Action
    action_label: str
    reason: str
    relevant_pollution_context: PollutionContext
    alternative_activity: str | None = None
    suggested_time: str | None = None
    suggested_at: datetime | None = None
    data_source: str
    attribution: list[str] = Field(default_factory=list)
    generated_at: datetime
    uncertainty_information: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    rule_id: str
    rule_version: str
    severity: Literal[
        "good",
        "satisfactory",
        "moderate",
        "poor",
        "very_poor",
        "severe",
        "info",
    ]
    confidence: Confidence


class FamilyPreferencesResponse(FamilyPreferences):
    household_id: UUID
    created_at: datetime
    updated_at: datetime


class AiExplanation(BaseModel):
    status: Literal["available", "unavailable", "rejected"]
    text: str | None = None
    model: str | None = None
    reason: str | None = None


class FamilyRecommendationBatch(BaseModel):
    household_id: UUID
    generated_at: datetime
    rules_version: str
    pollution_context: PollutionContext
    recommendations: list[FamilyRecommendation]
    ai_explanation: AiExplanation
    disclaimer: str


class FamilyRecommendationList(BaseModel):
    items: list[FamilyRecommendation]
    limit: int
    offset: int
