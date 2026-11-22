"""Versioned API router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    air,
    copilot,
    ecoroute,
    family,
    health,
    household,
    impact,
    indoor,
    locations,
    meta,
    routines,
    sessions,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(meta.router)
api_router.include_router(sessions.router)
api_router.include_router(locations.router)
api_router.include_router(air.router, prefix="/air-quality")
# Temporary alias for clients built against the earlier contract. The
# documented path is /air-quality; this alias is not advertised in OpenAPI.
api_router.include_router(air.router, prefix="/air", include_in_schema=False)
api_router.include_router(household.router)
api_router.include_router(family.router)
api_router.include_router(routines.router)
api_router.include_router(indoor.router)
api_router.include_router(ecoroute.router)
api_router.include_router(impact.router)
api_router.include_router(copilot.router)
