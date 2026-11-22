"""Household, member and preference contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AgeBand = Literal["0-5", "6-12", "13-17", "18-59", "60+"]
HealthFlag = Literal["asthma", "allergy", "copd", "heart", "pregnant"]
Dwelling = Literal["apartment_ground", "apartment_upper", "independent", "other"]
CookingFuel = Literal["lpg", "png", "induction", "biomass", "mixed", "other"]
Intensity = Literal["light", "moderate", "vigorous"]
Venue = Literal["outdoor", "indoor"]
ActivityType = Literal[
    "morning_exercise",
    "evening_exercise",
    "school_commute",
    "office_commute",
    "outdoor_play",
    "shopping",
    "walking",
    "cycling",
    "public_transport",
    "indoor_activity",
]
TransportMode = Literal["walk", "cycle", "public", "private", "mixed"]
Weekday = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

TIME_PATTERN = r"^([01]\d|2[0-3]):[0-5]\d$"
ALL_WEEKDAYS: tuple[Weekday, ...] = (
    "mon",
    "tue",
    "wed",
    "thu",
    "fri",
    "sat",
    "sun",
)


class Member(BaseModel):
    id: UUID
    age_band: AgeBand
    health_flags: list[HealthFlag]
    created_at: datetime


class MemberCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age_band: AgeBand
    health_flags: list[HealthFlag] = Field(default_factory=list, max_length=5)

    @field_validator("health_flags")
    @classmethod
    def _flags_are_unique(cls, value: list[HealthFlag]) -> list[HealthFlag]:
        if len(value) != len(set(value)):
            raise ValueError("health_flags must not contain duplicates.")
        return value


class MemberUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age_band: AgeBand | None = None
    health_flags: list[HealthFlag] | None = Field(default=None, max_length=5)


class HouseholdUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="Household", min_length=2, max_length=80)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    city: str | None = Field(default=None, max_length=120)
    timezone: str = Field(default="Asia/Kolkata", max_length=64)
    dwelling: Dwelling
    cooking_fuel: CookingFuel
    has_purifier: bool = False
    purifier_cadr: int | None = Field(default=None, ge=50, le=1500)
    room_area_m2: int | None = Field(default=None, ge=5, le=300)
    ceiling_m: float | None = Field(default=None, ge=2.0, le=5.0)

    @field_validator("timezone")
    @classmethod
    def _valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown IANA timezone.") from exc
        return value

    @field_validator("city")
    @classmethod
    def _clean_city(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Household name cannot be blank.")
        return cleaned


class Household(BaseModel):
    id: UUID
    name: str
    lat: float | None
    lon: float | None
    city: str | None
    timezone: str
    dwelling: Dwelling
    cooking_fuel: CookingFuel
    has_purifier: bool
    purifier_cadr: int | None
    room_area_m2: int | None
    ceiling_m: float | None
    members: list[Member]
    created_at: datetime
    updated_at: datetime


class ActivityWindow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=50)
    start: str = Field(pattern=TIME_PATTERN)
    duration_min: int = Field(ge=15, le=180)
    intensity: Intensity
    venue: Venue
    activity: ActivityType | None = None
    days: list[Weekday] = Field(
        default_factory=lambda: list(ALL_WEEKDAYS), min_length=1, max_length=7
    )
    flexibility_min: int = Field(default=60, ge=0, le=180)
    indoor_alternative: str | None = Field(default=None, max_length=80)
    transport_mode: TransportMode | None = None

    @field_validator("days")
    @classmethod
    def _days_are_unique(cls, value: list[Weekday]) -> list[Weekday]:
        if len(value) != len(set(value)):
            raise ValueError("days must not contain duplicates.")
        return value

    @field_validator("indoor_alternative")
    @classmethod
    def _clean_alternative(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class Preferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    locale: str = Field(default="en-IN", min_length=2, max_length=16)
    activity_windows: list[ActivityWindow] = Field(default_factory=list, max_length=12)
    alert_threshold_aqi: int = Field(default=150, ge=0, le=500)
    transport_mode: TransportMode = "mixed"
    notifications_enabled: bool = True
    notify_alerts: bool = True
    notify_daily_summary: bool = False
    quiet_hours_start: str | None = Field(default=None, pattern=TIME_PATTERN)
    quiet_hours_end: str | None = Field(default=None, pattern=TIME_PATTERN)

    @model_validator(mode="after")
    def _validate_preferences(self) -> Preferences:
        ids = [window.id for window in self.activity_windows]
        if len(ids) != len(set(ids)):
            raise ValueError("activity_windows ids must be unique.")
        if (self.quiet_hours_start is None) != (self.quiet_hours_end is None):
            raise ValueError(
                "quiet_hours_start and quiet_hours_end must be set together."
            )
        return self


class FamilyPreferences(Preferences):
    """Preferences used by the family engine; every window names an activity."""

    @model_validator(mode="after")
    def _activities_are_named(self) -> FamilyPreferences:
        missing = [
            window.id for window in self.activity_windows if window.activity is None
        ]
        if missing:
            raise ValueError(
                "Every activity window needs an activity type. Update: "
                + ", ".join(sorted(missing))
            )
        return self


class PreferencesResponse(Preferences):
    household_id: UUID
    created_at: datetime
    updated_at: datetime
