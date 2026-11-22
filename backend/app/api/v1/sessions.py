"""Anonymous session endpoints."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Depends, Response

from app.api.deps import (
    CurrentProfile,
    RequestIdDep,
    SessionDep,
    SettingsDep,
    public_rate_limit,
    session_rate_limit,
)
from app.schemas.envelope import Envelope, envelope
from app.schemas.sessions import (
    HealthConsentUpdate,
    SessionCreate,
    SessionCreated,
    SessionInfo,
)
from app.services import session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post(
    "",
    response_model=Envelope[SessionCreated],
    status_code=HTTPStatus.CREATED,
    summary="Create an anonymous session",
    description=(
        "Issues an opaque bearer token once. Only its SHA-256 digest is stored. "
        "No name, email or phone number is collected."
    ),
    responses={
        HTTPStatus.SERVICE_UNAVAILABLE: {
            "description": "Session storage is unavailable."
        },
        HTTPStatus.TOO_MANY_REQUESTS: {"description": "Rate limit exceeded."},
    },
)
async def create_session(
    payload: SessionCreate,
    session: SessionDep,
    settings: SettingsDep,
    request_id: RequestIdDep,
    _limit: None = Depends(public_rate_limit("sessions")),
) -> Envelope[SessionCreated]:
    created = await session_service.create(session, settings, payload)
    return envelope(created, request_id)


@router.get(
    "/me",
    response_model=Envelope[SessionInfo],
    summary="Read the current session",
    responses={
        HTTPStatus.UNAUTHORIZED: {"description": "Missing or invalid bearer token."},
    },
)
async def read_session(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
) -> Envelope[SessionInfo]:
    return envelope(await session_service.info(session, profile), request_id)


@router.post(
    "/me/consent",
    response_model=Envelope[SessionInfo],
    summary="Update health-data consent",
    description=(
        "Health details can only be stored after this returns a non-null "
        "health_consent_at."
    ),
)
async def update_consent(
    payload: HealthConsentUpdate,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("consent")),
) -> Envelope[SessionInfo]:
    info = await session_service.grant_health_consent(
        session, profile, health_consent=payload.health_consent
    )
    return envelope(info, request_id)


@router.delete(
    "/me",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Delete the session and all stored data",
    description=(
        "Deletes the household, conversations, activities and the profile. "
        "A privacy audit event is retained without any identifying link."
    ),
)
async def delete_session(
    profile: CurrentProfile,
    session: SessionDep,
    _limit: None = Depends(session_rate_limit("delete")),
) -> Response:
    await session_service.delete_all(session, profile)
    return Response(status_code=HTTPStatus.NO_CONTENT)
