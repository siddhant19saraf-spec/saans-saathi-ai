"""Typed FastAPI dependencies.

Routes depend on these aliases rather than reaching into request state, which
keeps the injection points replaceable in tests.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.database import Database
from app.core.exceptions import (
    DatabaseUnavailableError,
    RateLimitError,
    ServiceUnavailableError,
    UnauthorizedError,
)
from app.core.rate_limit import RateLimiter
from app.core.security import hash_token, parse_bearer
from app.integrations.ai.gemini import GeminiClient
from app.integrations.air_quality.base import AirQualityProvider
from app.integrations.air_quality.circuit import CircuitBreaker
from app.integrations.geocoding.client import GeocodingClient
from app.models.profile import Profile
from app.repositories import profiles as profiles_repo
from app.services.air_quality_service import AirQualityService, ProviderBinding
from app.services.location_service import LocationSearchService
from app.utils.cache import TTLCache


def get_app_settings(request: Request) -> Settings:
    # The app owns its settings; a global singleton would ignore per-app
    # configuration (and any test overrides).
    return cast(Settings, request.app.state.settings)


def get_database(request: Request) -> Database:
    return cast(Database, request.app.state.database)


def get_request_id(request: Request) -> str:
    return cast(str, getattr(request.state, "request_id", ""))


def get_client_ip(request: Request) -> str:
    if request.client is None:
        return "unknown"
    return request.client.host[:64]


def get_rate_limiter(request: Request) -> RateLimiter:
    return cast(RateLimiter, request.app.state.rate_limiter)


def get_air_provider(request: Request) -> AirQualityProvider:
    return cast(AirQualityProvider, request.app.state.air_provider)


def get_air_breaker(request: Request) -> CircuitBreaker:
    return cast(CircuitBreaker, request.app.state.air_breaker)


def get_air_bindings(request: Request) -> Mapping[str, ProviderBinding]:
    return cast(
        Mapping[str, ProviderBinding], getattr(request.app.state, "air_bindings", {})
    )


def get_geocoding_client(request: Request) -> GeocodingClient:
    return cast(GeocodingClient, request.app.state.geocoding_client)


def get_air_cache(request: Request) -> TTLCache[object]:
    return cast(TTLCache[object], request.app.state.air_cache)


def get_gemini(request: Request) -> GeminiClient | None:
    return cast(GeminiClient | None, request.app.state.gemini)


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
DatabaseDep = Annotated[Database, Depends(get_database)]
RequestIdDep = Annotated[str, Depends(get_request_id)]
ClientIpDep = Annotated[str, Depends(get_client_ip)]
RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]
AirProviderDep = Annotated[AirQualityProvider, Depends(get_air_provider)]
AirBreakerDep = Annotated[CircuitBreaker, Depends(get_air_breaker)]
AirBindingsDep = Annotated[Mapping[str, ProviderBinding], Depends(get_air_bindings)]
AirCacheDep = Annotated[TTLCache[object], Depends(get_air_cache)]
GeocodingClientDep = Annotated[GeocodingClient, Depends(get_geocoding_client)]
GeminiDep = Annotated[GeminiClient | None, Depends(get_gemini)]


async def get_session(database: DatabaseDep) -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped session, or fail with a safe 503."""
    if not database.is_configured:
        raise ServiceUnavailableError("The database is not configured.")
    async with database.session() as session:
        yield session


async def get_optional_session(
    database: DatabaseDep,
) -> AsyncIterator[AsyncSession | None]:
    """Yield a session when configured; otherwise permit public-only work."""
    if not database.is_configured:
        yield None
        return
    async with database.session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
OptionalSessionDep = Annotated[AsyncSession | None, Depends(get_optional_session)]


async def _lookup_profile(
    request: Request,
    session: AsyncSession | None,
) -> Profile | None:
    token = parse_bearer(request.headers.get("authorization"))
    if token is None:
        return None
    if session is None:
        raise DatabaseUnavailableError("Session storage is not configured.")
    profile = await profiles_repo.get_by_token_hash(session, hash_token(token))
    if profile is None:
        raise UnauthorizedError("The session token is invalid or expired.")
    return profile


async def get_current_profile(
    request: Request,
    session: SessionDep,
) -> Profile:
    profile = await _lookup_profile(request, session)
    if profile is None:
        raise UnauthorizedError("A bearer token is required for this endpoint.")
    return profile


async def get_optional_profile(
    request: Request,
    session: OptionalSessionDep,
) -> Profile | None:
    return await _lookup_profile(request, session)


CurrentProfile = Annotated[Profile, Depends(get_current_profile)]
OptionalProfile = Annotated[Profile | None, Depends(get_optional_profile)]


async def get_air_service(
    session: OptionalSessionDep,
    settings: SettingsDep,
    provider: AirProviderDep,
    breaker: AirBreakerDep,
    cache: AirCacheDep,
    bindings: AirBindingsDep,
) -> AirQualityService:
    return AirQualityService(
        settings=settings,
        provider=provider,
        breaker=breaker,
        cache=cache,
        session=session,
        bindings=bindings,
    )


AirServiceDep = Annotated[AirQualityService, Depends(get_air_service)]


async def get_location_service(
    settings: SettingsDep,
    client: GeocodingClientDep,
    cache: AirCacheDep,
) -> LocationSearchService:
    return LocationSearchService(client=client, cache=cache, settings=settings)


LocationServiceDep = Annotated[LocationSearchService, Depends(get_location_service)]


def public_rate_limit(
    bucket: str,
) -> Callable[..., Awaitable[None]]:
    async def dependency(
        request: Request,
        limiter: RateLimiterDep,
        settings: SettingsDep,
    ) -> None:
        retry_after = limiter.consume(
            f"public:{bucket}:{get_client_ip(request)}",
            limit=settings.rate_limit_public_per_minute,
            window_seconds=60,
        )
        if retry_after is not None:
            raise RateLimitError(retry_after)

    return dependency


def session_rate_limit(
    bucket: str,
    *,
    window_seconds: int = 60,
) -> Callable[..., Awaitable[None]]:
    async def dependency(
        profile: CurrentProfile,
        limiter: RateLimiterDep,
        settings: SettingsDep,
    ) -> None:
        limit = (
            settings.rate_limit_session_per_minute
            if window_seconds == 60
            else settings.copilot_messages_per_hour
        )
        retry_after = limiter.consume(
            f"session:{bucket}:{profile.id}",
            limit=limit,
            window_seconds=window_seconds,
        )
        if retry_after is not None:
            raise RateLimitError(retry_after)

    return dependency


def copilot_rate_limit() -> Callable[..., Awaitable[None]]:
    """20 messages/hour per session, or per IP for anonymous calls."""

    async def dependency(
        request: Request,
        profile: OptionalProfile,
        limiter: RateLimiterDep,
        settings: SettingsDep,
    ) -> None:
        principal = str(profile.id) if profile is not None else get_client_ip(request)
        retry_after = limiter.consume(
            f"copilot:{principal}",
            limit=settings.copilot_messages_per_hour,
            window_seconds=3600,
        )
        if retry_after is not None:
            raise RateLimitError(retry_after)

    return dependency


def family_generate_rate_limit() -> Callable[..., Awaitable[None]]:
    async def dependency(
        profile: CurrentProfile,
        limiter: RateLimiterDep,
        settings: SettingsDep,
    ) -> None:
        retry_after = limiter.consume(
            f"family-generate:{profile.id}",
            limit=settings.family_generations_per_hour,
            window_seconds=3600,
        )
        if retry_after is not None:
            raise RateLimitError(retry_after)

    return dependency


def indoor_explain_rate_limit() -> Callable[..., Awaitable[None]]:
    async def dependency(
        profile: CurrentProfile,
        limiter: RateLimiterDep,
        settings: SettingsDep,
    ) -> None:
        retry_after = limiter.consume(
            f"indoor-explain:{profile.id}",
            limit=settings.indoor_explanations_per_hour,
            window_seconds=3600,
        )
        if retry_after is not None:
            raise RateLimitError(retry_after)

    return dependency
