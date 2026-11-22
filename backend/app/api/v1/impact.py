"""Sustainability ledger endpoints."""

from __future__ import annotations

from http import HTTPStatus
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    CurrentProfile,
    RequestIdDep,
    SessionDep,
    public_rate_limit,
    session_rate_limit,
)
from app.schemas.envelope import Envelope, envelope
from app.schemas.impact import (
    Activity,
    ActivityCreate,
    BaselineSavings,
    FactorOut,
    GoalCreate,
    GoalOut,
    GoalUpdate,
    ImpactSummary,
    ImpactTrends,
    MethodologyOut,
)
from app.services import impact_service

router = APIRouter(prefix="/impact", tags=["impact"])

_LEDGER_ERRORS: dict[int | str, dict[str, Any]] = {
    HTTPStatus.UNAUTHORIZED: {"description": "Missing or invalid bearer token."},
    HTTPStatus.UNPROCESSABLE_ENTITY: {
        "description": (
            "No household profile, an unsupported activity type, a unit "
            "mismatch, or a duplicate activity. Unsupported types are "
            "rejected rather than estimated."
        )
    },
    HTTPStatus.TOO_MANY_REQUESTS: {"description": "Session rate limit exceeded."},
}


@router.get(
    "/factors",
    response_model=Envelope[list[FactorOut]],
    summary="List emission factors",
    description=(
        "Returns the versioned factor registry with its source URLs. Only "
        "factors with a verifiable source are listed."
    ),
    responses={
        HTTPStatus.TOO_MANY_REQUESTS: {"description": "Public rate limit exceeded."}
    },
)
async def list_factors(
    request_id: RequestIdDep,
    _limit: None = Depends(public_rate_limit("impact-factors")),
) -> Envelope[list[FactorOut]]:
    return envelope(impact_service.factors(), request_id)


@router.get(
    "/activities",
    response_model=Envelope[list[Activity]],
    summary="List logged activities",
    responses=_LEDGER_ERRORS,
)
async def list_activities(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0, le=100_000)] = 0,
) -> Envelope[list[Activity]]:
    rows = await impact_service.list_activities(
        session, profile, days=days, limit=limit, offset=offset
    )
    return envelope(rows, request_id)


@router.post(
    "/activities",
    response_model=Envelope[Activity],
    status_code=HTTPStatus.CREATED,
    summary="Log an activity",
    description=(
        "The stored CO2e uses the factor version recorded on the row. "
        "Activities without a verified factor are rejected with 422 "
        "FACTOR_NOT_AVAILABLE. Exact duplicate activity (same type, date, "
        "quantity) within the current day is rejected with DUPLICATE_ACTIVITY."
    ),
    responses=_LEDGER_ERRORS,
)
async def add_activity(
    payload: ActivityCreate,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("impact-write")),
) -> Envelope[Activity]:
    activity = await impact_service.add_activity(session, profile, payload)
    return envelope(activity, request_id)


@router.get(
    "/summary",
    response_model=Envelope[ImpactSummary],
    summary="Summarise logged impact",
    responses=_LEDGER_ERRORS,
)
async def read_summary(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> Envelope[ImpactSummary]:
    summary = await impact_service.summary(session, profile, days=days)
    return envelope(summary, request_id)


@router.get(
    "/baseline-savings",
    response_model=Envelope[BaselineSavings],
    summary="Estimated baseline and savings",
    description=(
        "Returns modelled baseline emissions versus logged activity emissions. "
        "The baseline is a documented assumption, never a measured value."
    ),
    responses=_LEDGER_ERRORS,
)
async def read_baseline_savings(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> Envelope[BaselineSavings]:
    savings = await impact_service.baseline_and_savings(session, profile, days=days)
    return envelope(savings, request_id)


@router.get(
    "/trends",
    response_model=Envelope[ImpactTrends],
    summary="Weekly and monthly impact trends",
    responses=_LEDGER_ERRORS,
)
async def read_trends(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> Envelope[ImpactTrends]:
    trends = await impact_service.trends(session, profile, days=days)
    return envelope(trends, request_id)


@router.get(
    "/methodology",
    response_model=Envelope[MethodologyOut],
    summary="Calculation methodology",
    description=(
        "Returns the formulas, factors, assumptions and limitations used for "
        "impact calculations."
    ),
    responses={
        HTTPStatus.TOO_MANY_REQUESTS: {"description": "Public rate limit exceeded."}
    },
)
async def read_methodology(
    request_id: RequestIdDep,
    _limit: None = Depends(public_rate_limit("impact-methodology")),
) -> Envelope[MethodologyOut]:
    return envelope(impact_service.methodology(), request_id)


@router.get(
    "/goals",
    response_model=Envelope[list[GoalOut]],
    summary="List sustainability goals",
    responses=_LEDGER_ERRORS,
)
async def list_goals(
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
) -> Envelope[list[GoalOut]]:
    goals = await impact_service.list_goals(session, profile)
    return envelope(goals, request_id)


@router.post(
    "/goals",
    response_model=Envelope[GoalOut],
    status_code=HTTPStatus.CREATED,
    summary="Create a sustainability goal",
    responses=_LEDGER_ERRORS,
)
async def create_goal(
    payload: GoalCreate,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("impact-write")),
) -> Envelope[GoalOut]:
    goal = await impact_service.create_goal(session, profile, payload)
    return envelope(goal, request_id)


@router.put(
    "/goals/{goal_id}",
    response_model=Envelope[GoalOut],
    summary="Update a sustainability goal",
    responses=_LEDGER_ERRORS,
)
async def update_goal(
    goal_id: UUID,
    payload: GoalUpdate,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("impact-write")),
) -> Envelope[GoalOut]:
    goal = await impact_service.update_goal(session, profile, goal_id, payload)
    return envelope(goal, request_id)


@router.delete(
    "/goals/{goal_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Delete a sustainability goal",
    responses=_LEDGER_ERRORS,
)
async def delete_goal(
    goal_id: UUID,
    profile: CurrentProfile,
    session: SessionDep,
    request_id: RequestIdDep,
    _limit: None = Depends(session_rate_limit("impact-write")),
) -> None:
    await impact_service.delete_goal(session, profile, goal_id)
    return None


__all__ = [
    "add_activity",
    "create_goal",
    "delete_goal",
    "list_activities",
    "list_factors",
    "list_goals",
    "read_baseline_savings",
    "read_methodology",
    "read_summary",
    "read_trends",
    "update_goal",
]
