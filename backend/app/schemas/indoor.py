"""IndoorShield request/response contracts.

The pre-existing mass-balance estimate contracts stay at the top of this module.
Everything added below belongs to the persisted assessment, sensor and action
workflow. Responses always distinguish measured sensor samples, modelled
outdoor context and deterministic recommendations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# -- existing modelled-estimate contracts ----------------------------------

RoomType = Literal[
    "living_room",
    "bedroom",
    "kitchen",
    "bathroom",
    "study",
    "children_room",
    "other",
]
VentilationType = Literal["windows", "exhaust", "mechanical", "none", "other"]
DampnessLevel = Literal["none", "occasional", "persistent", "unknown"]
SourceCode = Literal[
    "biomass_cooking",
    "gas_stove",
    "cooking_fumes",
    "candles_incense",
    "tobacco_smoke",
    "indoor_burning",
    "cleaning_products",
    "aerosol_sprays",
    "paints_solvents",
    "renovation_materials",
    "dust",
    "outdoor_infiltration",
    "poor_ventilation",
    "dampness",
    "mold_risk",
    "other",
]
SourceFrequency = Literal["once", "occasional", "weekly", "daily", "frequent"]
CleaningFrequency = Literal["daily", "weekly", "monthly", "less"]
CookingFuel = Literal["lpg", "png", "induction", "biomass", "mixed", "other"]
CookingLocation = Literal["indoor_kitchen", "separate_room", "outdoor", "other"]
DwellingType = Literal["apartment_ground", "apartment_upper", "independent", "other"]
CalibrationStatus = Literal["verified", "unverified", "unknown"]
ReadingQuality = Literal["valid", "suspect"]
ActionStatus = Literal["pending", "completed", "dismissed"]
ActionPriority = Literal["high", "medium", "low"]
RecommendationCategory = Literal[
    "cooking",
    "cleaning",
    "dust",
    "ventilation",
    "filtration",
    "humidity",
    "outdoor_pollution",
    "general",
]
ExplanationStatus = Literal["deterministic", "ai", "fallback"]
DataAvailability = Literal["available", "stale", "unavailable"]
SensorDataStatus = Literal["measured", "stale", "unavailable"]


class IndoorLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class IndoorOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purifier_cadr: int | None = Field(default=None, ge=0, le=1500)
    room_area_m2: float | None = Field(default=None, ge=5, le=300)
    ceiling_m: float | None = Field(default=None, ge=2.0, le=5.0)
    windows_open: bool = False
    cooking_fuel: (
        Literal["lpg", "png", "induction", "biomass", "mixed", "other"] | None
    ) = None


class IndoorAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location: IndoorLocation | None = None
    overrides: IndoorOverrides | None = None


class OutdoorContext(BaseModel):
    pm2_5: float
    provider: str
    observed_at: datetime | None
    stale: bool


class IndoorInterval(BaseModel):
    pm2_5_low: float
    pm2_5_high: float
    volume_m3: float
    purifier_cadr: int
    recommended_cadr: int


class VentilationWindow(BaseModel):
    start: datetime
    end: datetime
    pm2_5: float


class IndoorAction(BaseModel):
    id: str
    title: str
    detail: str


class IndoorAssessment(BaseModel):
    outdoor: OutdoorContext
    indoor: IndoorInterval
    ventilation: VentilationWindow | None
    actions: list[IndoorAction]
    assumptions: list[str]
    disclaimer: str


# -- assessment questionnaire ----------------------------------------------


class RoomInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=60)
    room_type: RoomType = "living_room"
    area_m2: float = Field(ge=3, le=500)
    ceiling_m: float = Field(default=2.7, ge=2.0, le=6.0)
    ventilation: VentilationType = "windows"
    windows_count: int = Field(default=1, ge=0, le=20)
    has_purifier: bool = False
    purifier_cadr: int | None = Field(default=None, ge=0, le=1500)
    dampness: DampnessLevel = "unknown"

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Room name cannot be blank.")
        return name

    @model_validator(mode="after")
    def _purifier_consistency(self) -> RoomInput:
        if self.purifier_cadr is not None and not self.has_purifier:
            raise ValueError("purifier_cadr requires has_purifier=true.")
        return self


class RoomOut(RoomInput):
    id: str


class SourceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: SourceCode
    frequency: SourceFrequency = "occasional"
    note: str | None = Field(default=None, max_length=200)


class SourceOut(SourceInput):
    id: str


class AssessmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dwelling: DwellingType
    cooking_fuel: CookingFuel
    cooking_location: CookingLocation = "indoor_kitchen"
    cooking_exhaust: bool = False
    cleaning_frequency: CleaningFrequency
    sensor_available: bool = False
    notes: str | None = Field(default=None, max_length=500)
    rooms: list[RoomInput] = Field(min_length=1, max_length=10)
    sources: list[SourceInput] = Field(default_factory=list, max_length=16)

    @model_validator(mode="after")
    def _unique_rooms_and_sources(self) -> AssessmentCreate:
        names = [room.name.casefold() for room in self.rooms]
        if len(names) != len(set(names)):
            raise ValueError("Room names must be unique within an assessment.")
        codes = [source.code for source in self.sources]
        if len(codes) != len(set(codes)):
            raise ValueError("Each indoor source can only be reported once.")
        return self


class AssessmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dwelling: DwellingType | None = None
    cooking_fuel: CookingFuel | None = None
    cooking_location: CookingLocation | None = None
    cooking_exhaust: bool | None = None
    cleaning_frequency: CleaningFrequency | None = None
    sensor_available: bool | None = None
    notes: str | None = Field(default=None, max_length=500)
    rooms: list[RoomInput] | None = Field(default=None, min_length=1, max_length=10)
    sources: list[SourceInput] | None = Field(default=None, max_length=16)

    @model_validator(mode="after")
    def _unique_when_present(self) -> AssessmentUpdate:
        if self.rooms is not None:
            names = [room.name.casefold() for room in self.rooms]
            if len(names) != len(set(names)):
                raise ValueError("Room names must be unique within an assessment.")
        if self.sources is not None:
            codes = [source.code for source in self.sources]
            if len(codes) != len(set(codes)):
                raise ValueError("Each indoor source can only be reported once.")
        return self


class ExplanationOut(BaseModel):
    status: ExplanationStatus
    text: str
    note: str | None = None
    model: str | None = None


class OutdoorSnapshotOut(BaseModel):
    available: bool = False
    provider: str | None = None
    observed_at: datetime | None = None
    stale: bool = False
    pm2_5: float | None = None
    pm10: float | None = None
    cpcb_aqi: int | None = None
    forecast_available: bool = False
    forecast_min_pm2_5: float | None = None
    forecast_min_at: datetime | None = None
    attribution: list[str] = Field(default_factory=list)
    note: str = ""


class RecommendationOut(BaseModel):
    id: str
    assessment_id: str
    rule_id: str
    category: RecommendationCategory
    title: str
    description: str
    issue: str
    action: str
    priority: ActionPriority
    priority_score: int
    evidence: str
    expected_benefit: str
    limitations: str
    frequency: Literal["once", "daily", "weekly", "monthly"]
    source: Literal["deterministic", "ai"]
    status: ActionStatus
    due_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ActionCounts(BaseModel):
    total: int = 0
    pending: int = 0
    completed: int = 0
    dismissed: int = 0
    high_priority: int = 0


class AssessmentOut(BaseModel):
    id: str
    household_id: str
    status: Literal["draft", "completed"]
    dwelling: DwellingType
    cooking_fuel: CookingFuel
    cooking_location: CookingLocation
    cooking_exhaust: bool
    cleaning_frequency: CleaningFrequency
    sensor_available: bool
    notes: str | None
    engine_version: str | None
    summary: str | None
    confidence: Literal["high", "medium", "low"] | None
    assumptions: list[str]
    limitations: list[str]
    outdoor_context: OutdoorSnapshotOut
    explanation: ExplanationOut
    rooms: list[RoomOut]
    sources: list[SourceOut]
    recommendations: list[RecommendationOut]
    action_counts: ActionCounts
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AssessmentList(BaseModel):
    assessments: list[AssessmentOut]
    count: int


class RecommendationList(BaseModel):
    recommendations: list[RecommendationOut]
    counts: ActionCounts


# -- sensors and readings ---------------------------------------------------


class SensorCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1, max_length=40)
    external_id: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=80)
    model: str | None = Field(default=None, max_length=80)
    room_name: str | None = Field(default=None, max_length=60)
    calibration_status: CalibrationStatus = "unknown"

    @field_validator("provider", "external_id", "name")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Value cannot be blank.")
        return text


class SensorReadingCreate(BaseModel):
    """A single sample reported by an integration.

    ``pollutant`` is a string so unsupported names receive an explicit
    UNSUPPORTED_POLLUTANT error instead of a generic schema failure.
    """

    model_config = ConfigDict(extra="forbid")

    pollutant: str = Field(min_length=1, max_length=16)
    value: float = Field(ge=0)
    unit: str = Field(min_length=1, max_length=16)
    measured_at: datetime
    calibration_status: CalibrationStatus | None = None
    quality_status: ReadingQuality = "valid"
    note: str | None = Field(default=None, max_length=200)

    @field_validator("pollutant")
    @classmethod
    def _normalise_pollutant(cls, value: str) -> str:
        return value.strip().casefold()

    @field_validator("unit")
    @classmethod
    def _normalise_unit(cls, value: str) -> str:
        # ``casefold`` maps the micro sign (U+00B5) to Greek mu (U+03BC).
        # Normalise both spellings before comparing with the canonical unit.
        return value.strip().casefold().replace("\u03bc", "\u00b5")

    @field_validator("measured_at")
    @classmethod
    def _require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("measured_at must include a UTC offset.")
        return value


class SensorReadingOut(BaseModel):
    id: str
    sensor_id: str
    pollutant: str
    value: float
    unit: str
    measured_at: datetime
    received_at: datetime
    calibration_status: CalibrationStatus
    quality_status: ReadingQuality
    stale: bool
    note: str | None


class SensorOut(BaseModel):
    id: str
    household_id: str
    provider: str
    external_id: str
    name: str
    model: str | None
    room_name: str | None
    calibration_status: CalibrationStatus
    status: Literal["active", "inactive"]
    last_seen_at: datetime | None
    latest_readings: list[SensorReadingOut]
    data_status: SensorDataStatus
    created_at: datetime


class SensorList(BaseModel):
    sensors: list[SensorOut]
    available: bool
    message: str


class SensorReadingList(BaseModel):
    sensor_id: str
    readings: list[SensorReadingOut]
    message: str | None = None


# -- action updates ---------------------------------------------------------


class ActionComplete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str | None = Field(default=None, max_length=300)


class ActionReschedule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    due_at: datetime
    note: str | None = Field(default=None, max_length=300)

    @field_validator("due_at")
    @classmethod
    def _require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("due_at must include a UTC offset.")
        return value


class ActionEventOut(BaseModel):
    id: str
    recommendation_id: str
    event_type: Literal["completed", "rescheduled", "reopened"]
    previous_due_at: datetime | None
    new_due_at: datetime | None
    note: str | None
    created_at: datetime


# -- overview ---------------------------------------------------------------


class IndoorDataStatus(BaseModel):
    assessment: Literal["completed", "missing"]
    indoor_sensors: SensorDataStatus
    outdoor: DataAvailability
    note: str


class IndoorOverview(BaseModel):
    latest_assessment: AssessmentOut | None
    sensors: SensorList
    outdoor: OutdoorSnapshotOut
    recommendations: list[RecommendationOut]
    action_counts: ActionCounts
    data_status: IndoorDataStatus
    disclaimer: str
    generated_at: datetime
