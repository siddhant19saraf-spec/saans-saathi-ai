"""Family profile, preferences and personalized recommendations.

Every route is scoped to the bearer-token profile. The deterministic rules
engine decides actions; the model only explains them. The single household per
anonymous session is a documented development limitation.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import (
    AirServiceDep,
    CurrentProfile,
    GeminiDep,
    RequestIdDep,
    SessionDep,
    SettingsDep,
    family_generate_rate_limit,
    session_rate_limit,
)
from app.schemas.envelope import Envelope, envelope
from app.schemas.family import (
    FamilyPreferencesResponse,
    FamilyProfile,
    FamilyProfileCreate,
    FamilyRecommendation,
    FamilyRecommendationBatch,
    FamilyRecommendationList,
)
from app.schemas.household import FamilyPreferences
from app.services import family_service

router = APIRouter(prefix="/family", tags=["family"])

_COMMON_ERRORS: dict[int | str, dict[str, Any]] = {
    HTTPStatus.UNAUTHORIZED: {"description": "Missing or invalid bearer token."},
    HTTPStatus.NOT_FOUND: {
        "description": "No family profile, preferences or recommendation exists."
    },
    HTTPStatus.CONFLICT: {
        "description": "A family profile already exists, or none exists yet."
    },
    HTTPStatus.UNPROCESSABLE_ENTITY: {
        "description": "Preferences or profile data cannot produce recommendations."
    },
    HTTPStatus.TOO_MANY_REQUESTS: {"description": "Session rate limit exceeded."},
}


@router.post(
    "/profile",
    response_model=Envelope[FamilyProfile],
    status_code=HTTPStatus.CREATED,
    summary="Create the family profile",
    description=(
        "Stores a household name, required coordinates, age bands and optional "
        "coarse health flags. Health flags require explicit health-data consent "
        "(403 CONSENT_REQUIRED otherwise). No member names are stored."
    ),
    responses={
        **_COMMON_ERRORS,
        HTTPStatus.FORBIDDEN: {"description": "Health-data consent is required."},
    },
)
async def create_profile(
    payload: FamilyProfileCreate,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("family-write")),
) -> Envelope[FamilyProfile]:
    return envelope(
        await family_service.create_profile(session, profile, payload), request_id
    )


@router.get(
    "/profile",
    response_model=Envelope[FamilyProfile],
    summary="Read the family profile",
    responses=_COMMON_ERRORS,
)
async def read_profile(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
) -> Envelope[FamilyProfile]:
    return envelope(await family_service.get_profile(session, profile), request_id)


@router.put(
    "/profile",
    response_model=Envelope[FamilyProfile],
    summary="Replace the family profile",
    description=(
        "Replaces household details and the full member list in one transaction. "
        "A missing profile returns 409; use POST to create it."
    ),
    responses=_COMMON_ERRORS,
)
async def update_profile(
    payload: FamilyProfileCreate,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("family-write")),
) -> Envelope[FamilyProfile]:
    return envelope(
        await family_service.update_profile(session, profile, payload), request_id
    )


@router.delete(
    "/profile",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Delete the family profile",
    description=(
        "Deletes the household, members, preferences, saved locations and every "
        "stored family recommendation for this session."
    ),
    responses=_COMMON_ERRORS,
)
async def delete_profile(
    profile: CurrentProfile,
    session: SessionDep,
    _limit: None = Depends(session_rate_limit("family-write")),
) -> Response:
    await family_service.delete_profile(session, profile)
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get(
    "/preferences",
    response_model=Envelope[FamilyPreferencesResponse],
    summary="Read family activity preferences",
    responses=_COMMON_ERRORS,
)
async def read_preferences(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
) -> Envelope[FamilyPreferencesResponse]:
    return envelope(await family_service.get_preferences(session, profile), request_id)


@router.put(
    "/preferences",
    response_model=Envelope[FamilyPreferencesResponse],
    summary="Replace family activity preferences",
    description=(
        "Every activity window must name one of the supported activities. Windows "
        "are evaluated in the household timezone."
    ),
    responses=_COMMON_ERRORS,
)
async def update_preferences(
    payload: FamilyPreferences,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("family-write")),
) -> Envelope[FamilyPreferencesResponse]:
    return envelope(
        await family_service.update_preferences(session, profile, payload),
        request_id,
    )


@router.post(
    "/recommendations/generate",
    response_model=Envelope[FamilyRecommendationBatch],
    summary="Generate recommendations for saved activities",
    description=(
        "Evaluates every activity window with the deterministic rules engine and "
        "optional Gemini explanation. Current readings are used when fresh; "
        "otherwise forecast data is used and labelled, or the result is an "
        "uncertainty-aware check-back state. Results are stored as history."
    ),
    responses=_COMMON_ERRORS,
)
async def generate_recommendations(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    settings: SettingsDep,
    air_service: AirServiceDep,
    gemini: GeminiDep,
    _limit: None = Depends(family_generate_rate_limit()),
) -> Envelope[FamilyRecommendationBatch]:
    return envelope(
        await family_service.generate(
            session,
            profile,
            settings=settings,
            air_service=air_service,
            gemini=gemini,
        ),
        request_id,
    )


@router.get(
    "/recommendations",
    response_model=Envelope[FamilyRecommendationList],
    summary="List stored family recommendations",
    responses=_COMMON_ERRORS,
)
async def list_recommendations(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0, le=10_000),
) -> Envelope[FamilyRecommendationList]:
    return envelope(
        await family_service.list_recommendations(
            session, profile, limit=limit, offset=offset
        ),
        request_id,
    )


@router.get(
    "/recommendations/{recommendation_id}",
    response_model=Envelope[FamilyRecommendation],
    summary="Read one stored family recommendation",
    responses=_COMMON_ERRORS,
)
async def read_recommendation(
    recommendation_id: UUID,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
) -> Envelope[FamilyRecommendation]:
    return envelope(
        await family_service.get_recommendation(session, profile, recommendation_id),
        request_id,
    )
