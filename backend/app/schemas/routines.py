"""SmartRoutine activity and plan contracts."""

from __future__ import annotations

from datetime import date as Date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ActivityCategory = Literal[
    "morning_walk",
    "outdoor_sports",
    "school_travel",
    "college_travel",
    "office_commute",
    "grocery_shopping",
    "outdoor_recreation",
    "indoor_exercise",
    "household_activity",
    "gardening",
    "other",
]
ActivityVenue = Literal["indoor", "outdoor"]
ActivityPriority = Literal["low", "medium", "high"]
ActivityIntensity = Literal["light", "moderate", "vigorous"]
ItemStatus = Literal["done", "skipped"]
PlanStatus = Literal["active", "superseded"]

TIME_PATTERN = r"^([01]\d|2[0-3]):[0-5]\d$"
PLAN_OPEN_MINUTE = 5 * 60
PLAN_CLOSE_MINUTE = 22 * 60
_INDOOR_ONLY = {"indoor_exercise", "household_activity"}
_OUTDOOR_ONLY = {
    "morning_walk",
    "outdoor_sports",
    "outdoor_recreation",
    "gardening",
}


def _minutes(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


class ActivityLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None = Field(default=None, max_length=120)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def _coordinates_together(self) -> ActivityLocation:
        if (self.lat is None) != (self.lon is None):
            raise ValueError("lat and lon must be provided together.")
        return self


class RoutineActivityInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=80)
    category: ActivityCategory
    duration_min: int = Field(ge=15, le=240)
    preferred_start: str = Field(pattern=TIME_PATTERN)
    earliest_start: str | None = Field(default=None, pattern=TIME_PATTERN)
    latest_start: str | None = Field(default=None, pattern=TIME_PATTERN)
    venue: ActivityVenue
    fixed: bool = False
    priority: ActivityPriority = "medium"
    intensity: ActivityIntensity = "light"
    member_ids: list[UUID] = Field(default_factory=list, max_length=20)
    location: ActivityLocation | None = None
    indoor_alternative: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("title", "indoor_alternative", "notes")
    @classmethod
    def _clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("member_ids")
    @classmethod
    def _members_are_unique(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("member_ids must not contain duplicates.")
        return value

    @model_validator(mode="after")
    def _window_is_possible(self) -> RoutineActivityInput:
        preferred = _minutes(self.preferred_start)
        earliest = (
            _minutes(self.earliest_start)
            if self.earliest_start is not None
            else preferred
        )
        latest = (
            _minutes(self.latest_start) if self.latest_start is not None else preferred
        )
        if not (earliest <= preferred <= latest):
            raise ValueError(
                "earliest_start must be at or before preferred_start, and "
                "preferred_start at or before latest_start."
            )
        if earliest < PLAN_OPEN_MINUTE:
            raise ValueError("earliest_start cannot be before 05:00.")
        if latest > PLAN_CLOSE_MINUTE:
            raise ValueError("latest_start cannot be after 22:00.")
        if preferred + self.duration_min > PLAN_CLOSE_MINUTE:
            raise ValueError("The activity must end by 22:00.")
        if self.category in _INDOOR_ONLY and self.venue != "indoor":
            raise ValueError(f"{self.category} must be an indoor activity.")
        if self.category in _OUTDOOR_ONLY and self.venue != "outdoor":
            raise ValueError(f"{self.category} must be an outdoor activity.")
        if self.location is not None:
            self.location = ActivityLocation.model_validate(self.location.model_dump())
        return self


class RoutineActivityCreate(RoutineActivityInput):
    pass


class RoutineActivityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=80)
    category: ActivityCategory | None = None
    duration_min: int | None = Field(default=None, ge=15, le=240)
    preferred_start: str | None = Field(default=None, pattern=TIME_PATTERN)
    earliest_start: str | None = Field(default=None, pattern=TIME_PATTERN)
    latest_start: str | None = Field(default=None, pattern=TIME_PATTERN)
    venue: ActivityVenue | None = None
    fixed: bool | None = None
    priority: ActivityPriority | None = None
    intensity: ActivityIntensity | None = None
    member_ids: list[UUID] | None = Field(default=None, max_length=20)
    location: ActivityLocation | None = None
    indoor_alternative: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=500)
    active: bool | None = None

    @field_validator("title", "indoor_alternative", "notes")
    @classmethod
    def _clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def _at_least_one_field(self) -> RoutineActivityUpdate:
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update.")
        return self


class RoutineActivity(BaseModel):
    id: UUID
    title: str
    category: str
    duration_min: int
    preferred_start: str
    earliest_start: str | None
    latest_start: str | None
    venue: str
    fixed: bool
    priority: str
    intensity: str
    member_ids: list[str]
    location: dict[str, Any] | None
    indoor_alternative: str | None
    notes: str | None
    active: bool
    created_at: datetime
    updated_at: datetime


class ActivityList(BaseModel):
    items: list[RoutineActivity]


class RoutineGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: Date | None = None
    refresh: bool = False


class RoutineItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ItemStatus


class RoutineActivityChange(BaseModel):
    """A manual change applied to one activity from a generated plan."""

    model_config = ConfigDict(extra="forbid")

    duration_min: int | None = Field(default=None, ge=15, le=240)
    preferred_start: str | None = Field(default=None, pattern=TIME_PATTERN)
    earliest_start: str | None = Field(default=None, pattern=TIME_PATTERN)
    latest_start: str | None = Field(default=None, pattern=TIME_PATTERN)
    venue: ActivityVenue | None = None
    fixed: bool | None = None
    priority: ActivityPriority | None = None
    cancel: bool = False

    @model_validator(mode="after")
    def _has_a_change(self) -> RoutineActivityChange:
        provided = {
            key
            for key in self.model_fields_set
            if key != "cancel" and getattr(self, key) is not None
        }
        if not provided and not self.cancel:
            raise ValueError("Provide a schedule change or set cancel=true.")
        if self.cancel and provided:
            raise ValueError("cancel cannot be combined with other changes.")
        return self


class RoutineReplanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: Date | None = None


class Rationale(BaseModel):
    template_id: str
    params: dict[str, Any] = Field(default_factory=dict)


class RoutineExposure(BaseModel):
    dose_ug: float
    index: int


class RoutineBlock(BaseModel):
    id: str
    activity_id: str
    title: str
    category: str
    start: str
    end: str
    start_at: datetime
    end_at: datetime
    duration_min: int
    venue: str
    priority: str
    intensity: str
    fixed: bool
    status: str
    override: bool
    basis: str
    exposure: RoutineExposure
    score: float
    pm2_5: float | None = None
    aqi: int | None = None
    aqi_basis: str = "none"
    threshold: int
    data_available: bool
    rationale: list[Rationale] = Field(default_factory=list)
    fact_refs: list[str] = Field(default_factory=list)
    indoor_alternative: str | None = None
    member_ids: list[str] = Field(default_factory=list)


class RoutineAlternative(BaseModel):
    block_id: str
    activity_id: str
    kind: str
    start: str
    end: str
    start_at: datetime
    end_at: datetime
    venue: str
    dose_ug: float
    score: float
    pm2_5: float | None = None
    aqi: int | None = None
    aqi_basis: str = "none"
    rationale: list[Rationale] = Field(default_factory=list)


class RoutineUnscheduled(BaseModel):
    activity_id: str
    title: str
    category: str
    priority: str
    reason_code: str
    reason: str
    rationale: list[Rationale] = Field(default_factory=list)


class ForecastStatus(BaseModel):
    available: bool
    provider: str
    source_type: str
    issued_at: str | None
    stale: bool
    coverage_hours: int
    expected_hours: int
    coverage_ratio: float
    pm2_5_hours: int
    age_minutes: int | None
    basis: Literal["forecast"]


class ObservationStatus(BaseModel):
    provider: str | None = None
    source_type: str | None = None
    observed_at: datetime | None = None
    age_minutes: int | None = None
    stale: bool = False
    cpcb_aqi: int | None = None
    pm2_5: float | None = None


class RoutineDataStatus(BaseModel):
    forecast: ForecastStatus
    observation: ObservationStatus | None = None
    confidence: str
    notes: list[str] = Field(default_factory=list)


class RoutineScoring(BaseModel):
    version: str
    formula: str
    lower_is_better: bool
    weights: dict[str, Any]
    thresholds: dict[str, Any]
    assumptions: list[str]


class RoutineExplanation(BaseModel):
    status: Literal["ai", "deterministic"]
    text: str
    model: str | None = None
    note: str | None = None


class RoutinePlan(BaseModel):
    id: UUID
    date: Date
    timezone: str
    location: dict[str, Any] | None = None
    engine_version: str
    version: int
    status: PlanStatus
    parent_routine_id: UUID | None = None
    confidence: str
    blocks: list[RoutineBlock]
    unscheduled: list[RoutineUnscheduled]
    alternatives: list[RoutineAlternative]
    data_status: RoutineDataStatus
    scoring: RoutineScoring
    uncertainty: list[str]
    explanation: RoutineExplanation
    generated_at: datetime
    expires_at: datetime


class RoutineVersionSummary(BaseModel):
    id: UUID
    date: Date
    version: int
    status: PlanStatus
    confidence: str
    scheduled_count: int
    unscheduled_count: int
    engine_version: str
    generated_at: datetime


class RoutineHistory(BaseModel):
    items: list[RoutineVersionSummary]
    limit: int
    offset: int
    total: int
