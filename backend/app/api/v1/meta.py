"""Operational metadata for clients and dashboards.

Only names and booleans are exposed; no credential, host name, connection
string or upstream URL is included.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import (
    AirBreakerDep,
    AirProviderDep,
    RequestIdDep,
    SettingsDep,
)
from app.schemas.envelope import Envelope, envelope
from app.schemas.meta import Meta, ProviderMeta

router = APIRouter(tags=["meta"])


@router.get(
    "/meta",
    response_model=Envelope[Meta],
    summary="Service capabilities and limits",
)
async def read_meta(
    settings: SettingsDep,
    provider: AirProviderDep,
    breaker: AirBreakerDep,
    request_id: RequestIdDep,
) -> Envelope[Meta]:
    return envelope(
        Meta(
            service=settings.app_name,
            version=settings.app_version,
            environment=settings.app_env,
            ai_configured=settings.ai_configured,
            ai_model=settings.gemini_model,
            air_provider=ProviderMeta(
                name=provider.name,
                configured=True,
                circuit_state=breaker.state,
            ),
            limits={
                "request_max_bytes": settings.request_max_bytes,
                "public_requests_per_minute": settings.rate_limit_public_per_minute,
                "session_requests_per_minute": settings.rate_limit_session_per_minute,
                "copilot_messages_per_hour": settings.copilot_messages_per_hour,
                "session_ttl_days": settings.session_ttl_days,
            },
        ),
        request_id,
    )
