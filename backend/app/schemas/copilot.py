"""Copilot contracts, pinned to the frontend Zod schema."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

Confidence = Literal["high", "medium", "low"]


class CopilotContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class CopilotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=800)
    conversation_id: UUID | None = None
    context: CopilotContext | None = None

    @field_validator("message")
    @classmethod
    def _clean_message(cls, value: str) -> str:
        cleaned = "".join(char for char in value if char.isprintable() or char == "\n")
        cleaned = cleaned.strip()
        if not cleaned:
            raise ValueError("message cannot be empty")
        if cleaned.count("http") > 4:
            raise ValueError("message contains too many links")
        return cleaned


class CopilotAction(BaseModel):
    title: str
    detail: str
    time_window: str | None
    fact_refs: list[str]
    confidence: Confidence | None


class CopilotAvoid(BaseModel):
    title: str
    reason_fact_ref: str | None


class CopilotCitation(BaseModel):
    fact_id: str
    label: str
    value: float | str | None
    unit: str | None
    source: str
    observed_at: datetime | None


class CopilotAnswer(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    severity: str | None
    actions: list[CopilotAction]
    avoid: list[CopilotAvoid]
    citations: list[CopilotCitation]
    source: str
    model: str | None
    latency_ms: int | None
    disclaimer: str


class CopilotMessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    structured: dict[str, object] | None = None
    created_at: datetime


# --- Tool request schema -------------------------------------------------------


class CopilotToolArgument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str | None = None
    value: str | float | int | None = None


class CopilotToolRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(min_length=1, max_length=64)
    arguments: dict[str, Any] = Field(default_factory=dict)

    @field_validator("tool_name")
    @classmethod
    def _valid_tool_name(cls, value: str) -> str:
        allowed = {
            "get_air_quality",
            "get_air_quality_forecast",
            "get_household_profile",
            "get_family_recommendations",
            "get_daily_routine",
            "get_indoor_assessment",
            "get_indoor_recommendations",
            "compare_transport_options",
            "get_impact_summary",
            "get_sustainability_goals",
        }
        if value not in allowed:
            raise ValueError(
                f"Unsupported tool name '{value}'. Allowed: {', '.join(sorted(allowed))}"
            )
        return value
