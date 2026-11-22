"""IndoorShield assessment, monitoring and action endpoints.

The existing public ``POST /indoor/assess`` mass-balance estimate remains
unchanged. The routes below require a bearer session because every row is
scoped to the authenticated household.
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
    OptionalProfile,
    OptionalSessionDep,
    RequestIdDep,
    SessionDep,
    SettingsDep,
    indoor_explain_rate_limit,
    public_rate_limit,
    session_rate_limit,
)
from app.schemas.envelope import Envelope, envelope
from app.schemas.indoor import (
    ActionComplete,
    ActionEventOut,
    ActionReschedule,
    AssessmentCreate,
    AssessmentList,
    AssessmentOut,
    AssessmentUpdate,
    IndoorAssessment,
    IndoorAssessmentRequest,
    IndoorOverview,
    RecommendationList,
    RecommendationOut,
    SensorCreate,
    SensorList,
    SensorOut,
    SensorReadingCreate,
    SensorReadingList,
    SensorReadingOut,
)
from app.services import indoor_service, indoor_shield_service

router = APIRouter(prefix="/indoor", tags=["indoor"])

_COMMON_ERRORS: dict[int | str, dict[str, Any]] = {
    HTTPStatus.UNAUTHORIZED: {"description": "Missing or invalid bearer token."},
    HTTPStatus.NOT_FOUND: {
        "description": "The resource does not belong to this household."
    },
    HTTPStatus.UNPROCESSABLE_ENTITY: {
        "description": "The household profile or request data cannot be processed."
    },
    HTTPStatus.TOO_MANY_REQUESTS: {"description": "Rate limit exceeded."},
}


@router.post(
    "/assess",
    response_model=Envelope[IndoorAssessment],
    summary="Estimate indoor PM2.5",
    description=(
        "Combines the outdoor reading with a mass-balance interval. The result "
        "is a range with stated assumptions, not a sensor measurement. A saved "
        "household supplies defaults; the request may override room and purifier "
        "parameters. No profile data is persisted by this endpoint."
    ),
    responses={
        422: {
            "description": (
                "No location is available, or the provider did not report PM2.5. "
                "Codes: NO_LOCATION, OUTDOOR_PM25_UNAVAILABLE."
            )
        },
        429: {"description": "Public rate limit exceeded."},
        503: {"description": "Air-quality data is unavailable."},
    },
)
async def assess_indoor(
    payload: IndoorAssessmentRequest,
    profile: OptionalProfile,
    session: OptionalSessionDep,
    air_service: AirServiceDep,
    request_id: RequestIdDep,
    _limit: None = Depends(public_rate_limit("indoor")),
) -> Envelope[IndoorAssessment]:
    assessment = await indoor_service.assess(session, profile, payload, air_service)
    return envelope(assessment, request_id)


# -- assessments ------------------------------------------------------------


@router.post(
    "/assessments",
    response_model=Envelope[AssessmentOut],
    status_code=HTTPStatus.CREATED,
    summary="Create and evaluate an IndoorShield assessment",
    description=(
        "Stores the questionnaire, rooms and reported indoor sources, gathers "
        "validated indoor sensor samples and outdoor context, then generates "
        "deterministic recommendations. Self-reported information is never "
        "presented as a measurement."
    ),
    responses=_COMMON_ERRORS,
)
async def create_assessment(
    payload: AssessmentCreate,
    profile: CurrentProfile,
    session: SessionDep,
    air_service: AirServiceDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("indoor-write")),
) -> Envelope[AssessmentOut]:
    assessment = await indoor_shield_service.create_assessment(
        session, profile, payload, air_service
    )
    return envelope(assessment, request_id)


@router.get(
    "/assessments",
    response_model=Envelope[AssessmentList],
    summary="List IndoorShield assessments",
    responses=_COMMON_ERRORS,
)
async def list_assessments(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> Envelope[AssessmentList]:
    assessments = await indoor_shield_service.list_assessments(
        session, profile, limit=limit, offset=offset
    )
    return envelope(assessments, request_id)


@router.get(
    "/assessments/{assessment_id}",
    response_model=Envelope[AssessmentOut],
    summary="Read one IndoorShield assessment",
    responses=_COMMON_ERRORS,
)
async def get_assessment(
    assessment_id: UUID,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
) -> Envelope[AssessmentOut]:
    assessment = await indoor_shield_service.get_assessment(
        session, profile, assessment_id
    )
    return envelope(assessment, request_id)


@router.patch(
    "/assessments/{assessment_id}",
    response_model=Envelope[AssessmentOut],
    summary="Update and re-evaluate an assessment",
    description=(
        "Updates the questionnaire or replaces the room/source list, then "
        "regenerates pending recommendations. Completed action history is kept."
    ),
    responses=_COMMON_ERRORS,
)
async def update_assessment(
    assessment_id: UUID,
    payload: AssessmentUpdate,
    profile: CurrentProfile,
    session: SessionDep,
    air_service: AirServiceDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("indoor-write")),
) -> Envelope[AssessmentOut]:
    assessment = await indoor_shield_service.update_assessment(
        session, profile, assessment_id, payload, air_service
    )
    return envelope(assessment, request_id)


@router.delete(
    "/assessments/{assessment_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Delete an assessment",
    description="Deletes the assessment, its reported sources and its recommendations.",
    responses=_COMMON_ERRORS,
)
async def delete_assessment(
    assessment_id: UUID,
    profile: CurrentProfile,
    session: SessionDep,
    _limit: None = Depends(session_rate_limit("indoor-write")),
) -> Response:
    await indoor_shield_service.delete_assessment(session, profile, assessment_id)
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post(
    "/assessments/{assessment_id}/refresh",
    response_model=Envelope[AssessmentOut],
    summary="Re-evaluate with current sensor and outdoor data",
    responses=_COMMON_ERRORS,
)
async def refresh_assessment(
    assessment_id: UUID,
    profile: CurrentProfile,
    session: SessionDep,
    air_service: AirServiceDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("indoor-write")),
) -> Envelope[AssessmentOut]:
    assessment = await indoor_shield_service.refresh_assessment(
        session, profile, assessment_id, air_service
    )
    return envelope(assessment, request_id)


@router.post(
    "/assessments/{assessment_id}/explain",
    response_model=Envelope[AssessmentOut],
    summary="Explain the generated plan",
    description=(
        "Gemini may only rephrase the validated, deterministic plan. A missing "
        "key, exhausted budget, provider failure or rejected output falls back "
        "to the deterministic summary. The model never receives raw household "
        "notes or coordinates and never creates measurements."
    ),
    responses=_COMMON_ERRORS,
)
async def explain_assessment(
    assessment_id: UUID,
    profile: CurrentProfile,
    session: SessionDep,
    settings: SettingsDep,
    gemini: GeminiDep,
    request_id: RequestIdDep,
    _limit: None = Depends(indoor_explain_rate_limit()),
) -> Envelope[AssessmentOut]:
    assessment = await indoor_shield_service.explain_assessment(
        session, profile, assessment_id, settings=settings, gemini=gemini
    )
    return envelope(assessment, request_id)


# -- overview and recommendations ------------------------------------------


@router.get(
    "/overview",
    response_model=Envelope[IndoorOverview],
    summary="Read the IndoorShield dashboard",
    description=(
        "Returns the latest assessment, action summary, sensor availability and "
        "outdoor context. Unavailable measurements are explicit."
    ),
    responses=_COMMON_ERRORS,
)
async def overview(
    profile: CurrentProfile,
    session: SessionDep,
    air_service: AirServiceDep,
    request_id: RequestIdDep,
) -> Envelope[IndoorOverview]:
    data = await indoor_shield_service.overview(session, profile, air_service)
    return envelope(data, request_id)


@router.get(
    "/recommendations",
    response_model=Envelope[RecommendationList],
    summary="List indoor recommendations",
    responses=_COMMON_ERRORS,
)
async def list_recommendations(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    assessment_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Envelope[RecommendationList]:
    data = await indoor_shield_service.list_recommendations(
        session,
        profile,
        assessment_id=assessment_id,
        limit=limit,
        offset=offset,
    )
    return envelope(data, request_id)


@router.post(
    "/recommendations/{recommendation_id}/complete",
    response_model=Envelope[RecommendationOut],
    summary="Mark an indoor action complete",
    responses=_COMMON_ERRORS,
)
async def complete_action(
    recommendation_id: UUID,
    payload: ActionComplete,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("indoor-action")),
) -> Envelope[RecommendationOut]:
    action = await indoor_shield_service.complete_action(
        session, profile, recommendation_id, note=payload.note
    )
    return envelope(action, request_id)


@router.post(
    "/recommendations/{recommendation_id}/reschedule",
    response_model=Envelope[RecommendationOut],
    summary="Reschedule a pending indoor action",
    responses=_COMMON_ERRORS,
)
async def reschedule_action(
    recommendation_id: UUID,
    payload: ActionReschedule,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("indoor-action")),
) -> Envelope[RecommendationOut]:
    action = await indoor_shield_service.reschedule_action(
        session,
        profile,
        recommendation_id,
        due_at=payload.due_at,
        note=payload.note,
    )
    return envelope(action, request_id)


@router.post(
    "/recommendations/{recommendation_id}/reopen",
    response_model=Envelope[RecommendationOut],
    summary="Reopen a completed indoor action",
    responses=_COMMON_ERRORS,
)
async def reopen_action(
    recommendation_id: UUID,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("indoor-action")),
) -> Envelope[RecommendationOut]:
    action = await indoor_shield_service.reopen_action(
        session, profile, recommendation_id
    )
    return envelope(action, request_id)


@router.get(
    "/recommendations/{recommendation_id}/events",
    response_model=Envelope[list[ActionEventOut]],
    summary="Read indoor action history",
    responses=_COMMON_ERRORS,
)
async def action_events(
    recommendation_id: UUID,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
) -> Envelope[list[ActionEventOut]]:
    events = await indoor_shield_service.action_events(
        session, profile, recommendation_id
    )
    return envelope(events, request_id)


# -- sensors ----------------------------------------------------------------


@router.get(
    "/sensors",
    response_model=Envelope[SensorList],
    summary="List registered indoor sensors",
    description=(
        "Returns explicit availability. With no registered device the message "
        "is 'Indoor sensor data unavailable.' and no measurements are invented."
    ),
    responses=_COMMON_ERRORS,
)
async def list_sensors(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
) -> Envelope[SensorList]:
    sensors = await indoor_shield_service.list_sensors(session, profile)
    return envelope(sensors, request_id)


@router.post(
    "/sensors",
    response_model=Envelope[SensorOut],
    status_code=HTTPStatus.CREATED,
    summary="Register an indoor sensor",
    description=(
        "Registers a provider-issued device identity. Registration alone does "
        "not create readings; the provider integration must submit validated "
        "samples."
    ),
    responses=_COMMON_ERRORS,
)
async def register_sensor(
    payload: SensorCreate,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("indoor-sensor-write")),
) -> Envelope[SensorOut]:
    sensor = await indoor_shield_service.register_sensor(session, profile, payload)
    return envelope(sensor, request_id)


@router.delete(
    "/sensors/{sensor_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Deactivate an indoor sensor",
    description="Keeps the measured history but stops future ingestion.",
    responses=_COMMON_ERRORS,
)
async def deactivate_sensor(
    sensor_id: UUID,
    profile: CurrentProfile,
    session: SessionDep,
    _limit: None = Depends(session_rate_limit("indoor-sensor-write")),
) -> Response:
    await indoor_shield_service.deactivate_sensor(session, profile, sensor_id)
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post(
    "/sensors/{sensor_id}/readings",
    response_model=Envelope[SensorReadingOut],
    status_code=HTTPStatus.CREATED,
    summary="Record a validated indoor reading",
    description=(
        "Accepts only supported pollutants with the canonical unit and a "
        "plausible value. The sample is stored with its timestamp, calibration "
        "status and quality status. Nothing is estimated."
    ),
    responses=_COMMON_ERRORS,
)
async def record_reading(
    sensor_id: UUID,
    payload: SensorReadingCreate,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("indoor-sensor-write")),
) -> Envelope[SensorReadingOut]:
    reading = await indoor_shield_service.record_reading(
        session, profile, sensor_id, payload
    )
    return envelope(reading, request_id)


@router.get(
    "/sensors/{sensor_id}/readings",
    response_model=Envelope[SensorReadingList],
    summary="List readings for one sensor",
    responses=_COMMON_ERRORS,
)
async def sensor_readings(
    sensor_id: UUID,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    limit: int = Query(default=100, ge=1, le=500),
) -> Envelope[SensorReadingList]:
    readings = await indoor_shield_service.sensor_readings(
        session, profile, sensor_id, limit=limit
    )
    return envelope(readings, request_id)
