"""Household profile, members, preferences and saved locations.

Every route is scoped to the bearer-token profile; identifiers from the path
are validated against that household before any change.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.api.deps import (
    CurrentProfile,
    RequestIdDep,
    SessionDep,
    session_rate_limit,
)
from app.schemas.envelope import Envelope, envelope
from app.schemas.household import (
    Household,
    HouseholdUpsert,
    Member,
    MemberCreate,
    MemberUpdate,
    Preferences,
    PreferencesResponse,
)
from app.schemas.locations import SavedLocation, SavedLocationCreate
from app.services import household_service

router = APIRouter(prefix="/household", tags=["household"])

_COMMON_ERRORS: dict[int | str, dict[str, Any]] = {
    HTTPStatus.UNAUTHORIZED: {"description": "Missing or invalid bearer token."},
    HTTPStatus.NOT_FOUND: {
        "description": "No household profile exists for this session."
    },
    HTTPStatus.CONFLICT: {
        "description": "Household state prevents the operation (for example, missing household)."
    },
    HTTPStatus.TOO_MANY_REQUESTS: {"description": "Session rate limit exceeded."},
}


@router.get(
    "",
    response_model=Envelope[Household],
    summary="Read the household profile",
    responses=_COMMON_ERRORS,
)
async def read_household(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
) -> Envelope[Household]:
    return envelope(await household_service.get(session, profile), request_id)


@router.put(
    "",
    response_model=Envelope[Household],
    summary="Create or replace the household profile",
    description=(
        "Upserts the household for the current session. Preferences are created "
        "on demand. Member rows are managed separately."
    ),
    responses=_COMMON_ERRORS,
)
async def upsert_household(
    payload: HouseholdUpsert,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("household-write")),
) -> Envelope[Household]:
    return envelope(
        await household_service.upsert(session, profile, payload), request_id
    )


@router.post(
    "/members",
    response_model=Envelope[Member],
    status_code=HTTPStatus.CREATED,
    summary="Add a household member",
    description=(
        "Age band and health flags only; no name or identifier is stored. "
        "Health flags require explicit health-data consent and return 403 "
        "CONSENT_REQUIRED otherwise."
    ),
    responses={
        **_COMMON_ERRORS,
        HTTPStatus.FORBIDDEN: {"description": "Health-data consent is required."},
    },
)
async def add_member(
    payload: MemberCreate,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("household-write")),
) -> Envelope[Member]:
    household = await household_service.require_household(session, profile)
    member = await household_service.add_member(
        session, profile, household=household, payload=payload
    )
    return envelope(member, request_id)


@router.patch(
    "/members/{member_id}",
    response_model=Envelope[Member],
    summary="Update a household member",
    responses={
        **_COMMON_ERRORS,
        HTTPStatus.FORBIDDEN: {"description": "Health-data consent is required."},
    },
)
async def update_member(
    member_id: UUID,
    payload: MemberUpdate,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("household-write")),
) -> Envelope[Member]:
    household = await household_service.require_household(session, profile)
    member = await household_service.update_member(
        session,
        profile,
        household=household,
        member_id=member_id,
        payload=payload,
    )
    return envelope(member, request_id)


@router.delete(
    "/members/{member_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Remove a household member",
    responses=_COMMON_ERRORS,
)
async def delete_member(
    member_id: UUID,
    profile: CurrentProfile,
    session: SessionDep,
    _limit: None = Depends(session_rate_limit("household-write")),
) -> Response:
    household = await household_service.require_household(session, profile)
    await household_service.delete_member(
        session, household=household, member_id=member_id
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get(
    "/preferences",
    response_model=Envelope[PreferencesResponse],
    summary="Read household preferences",
    responses=_COMMON_ERRORS,
)
async def read_preferences(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
) -> Envelope[PreferencesResponse]:
    return envelope(
        await household_service.get_preferences(session, profile), request_id
    )


@router.put(
    "/preferences",
    response_model=Envelope[PreferencesResponse],
    summary="Replace household preferences",
    description=(
        "Activity windows drive routine generation and are evaluated in the "
        "household timezone."
    ),
    responses=_COMMON_ERRORS,
)
async def update_preferences(
    payload: Preferences,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("household-write")),
) -> Envelope[PreferencesResponse]:
    return envelope(
        await household_service.update_preferences(session, profile, payload),
        request_id,
    )


@router.get(
    "/locations",
    response_model=Envelope[list[SavedLocation]],
    summary="List saved locations",
    responses=_COMMON_ERRORS,
)
async def list_locations(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
) -> Envelope[list[SavedLocation]]:
    return envelope(
        await household_service.list_locations(session, profile), request_id
    )


@router.post(
    "/locations",
    response_model=Envelope[SavedLocation],
    status_code=HTTPStatus.CREATED,
    summary="Save a location",
    description="Labels are unique per household; duplicates return 409.",
    responses=_COMMON_ERRORS,
)
async def add_location(
    payload: SavedLocationCreate,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("household-write")),
) -> Envelope[SavedLocation]:
    return envelope(
        await household_service.add_location(session, profile, payload), request_id
    )


@router.delete(
    "/locations/{location_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Delete a saved location",
    responses=_COMMON_ERRORS,
)
async def delete_location(
    location_id: UUID,
    profile: CurrentProfile,
    session: SessionDep,
    _limit: None = Depends(session_rate_limit("household-write")),
) -> Response:
    await household_service.delete_location(session, profile, location_id)
    return Response(status_code=HTTPStatus.NO_CONTENT)
