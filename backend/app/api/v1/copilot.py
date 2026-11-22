"""Grounded Copilot chat endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import (
    AirServiceDep,
    GeminiDep,
    OptionalProfile,
    OptionalSessionDep,
    RequestIdDep,
    SettingsDep,
    copilot_rate_limit,
)
from app.schemas.copilot import CopilotAnswer, CopilotRequest, CopilotToolRequest
from app.schemas.envelope import Envelope, envelope
from app.services import copilot_service

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post(
    "/chat",
    response_model=Envelope[CopilotAnswer],
    summary="Ask the grounded Copilot",
    description=(
        "Answers are constrained to a server-built FactPack. Numeric claims must "
        "cite fact ids; citations and sources are rebuilt server-side. Without "
        "a model key, or when model output fails validation, a deterministic "
        "answer is returned and source is 'deterministic'. Anonymous calls are "
        "accepted but not persisted; a posted conversation_id must belong to "
        "the bearer-token profile or the request returns 404."
    ),
    responses={
        404: {"description": "The conversation does not belong to this session."},
        422: {"description": "Invalid message or context."},
        429: {"description": "Copilot message limit exceeded."},
    },
)
async def chat(
    payload: CopilotRequest,
    profile: OptionalProfile,
    session: OptionalSessionDep,
    settings: SettingsDep,
    air_service: AirServiceDep,
    gemini: GeminiDep,
    request_id: RequestIdDep,
    _limit: None = Depends(copilot_rate_limit()),
) -> Envelope[CopilotAnswer]:
    answer = await copilot_service.chat(
        session,
        profile,
        payload,
        settings=settings,
        air_service=air_service,
        gemini=gemini,
    )
    return envelope(answer, request_id)


@router.post(
    "/tool-request",
    response_model=Envelope[dict[str, Any]],
    summary="Request a tool from the Copilot backend",
    description=(
        "The Copilot model may request backend tools (air-quality data, household "
        "profile, routine schedule, impact summary, sustainability goals, etc.). "
        "The backend executes the tool with proper authorisation and returns the "
        "result for the model to incorporate into its next response."
    ),
    responses={
        400: {"description": "Unknown tool or invalid arguments."},
        401: {"description": "Unauthorised: profile ID mismatch."},
        429: {"description": "Copilot tool limit exceeded."},
    },
)
async def tool_request(
    payload: CopilotToolRequest,
    profile: OptionalProfile,
    session: OptionalSessionDep,
    settings: SettingsDep,
    air_service: AirServiceDep,
    request_id: RequestIdDep,
    _limit: None = Depends(copilot_rate_limit()),
) -> Envelope[dict[str, Any]]:
    from app.services.copilot_service import request_tool as _request_tool

    result = await _request_tool(
        tool_name=payload.tool_name,
        arguments=payload.arguments,
        profile=profile,
        session=session,
        air_service=air_service,
    )
    return envelope(result, request_id)
