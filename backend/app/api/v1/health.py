"""Health endpoint (unversioned behaviour, served under the API prefix)."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.deps import DatabaseDep, SettingsDep
from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health",
    responses={
        HTTPStatus.SERVICE_UNAVAILABLE: {
            "model": HealthResponse,
            "description": "A configured dependency is unreachable.",
        }
    },
)
async def read_health(settings: SettingsDep, database: DatabaseDep) -> JSONResponse:
    result = await HealthService(settings, database).check()
    status_code = (
        HTTPStatus.SERVICE_UNAVAILABLE
        if result.status == "unhealthy"
        else HTTPStatus.OK
    )
    return JSONResponse(
        status_code=status_code,
        content=result.model_dump(mode="json"),
    )
