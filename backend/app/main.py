"""Application factory and lifespan management."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.database import Database
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import BodySizeLimitMiddleware, RequestContextMiddleware
from app.core.rate_limit import RateLimiter
from app.integrations.ai.gemini import GeminiClient
from app.integrations.air_quality.circuit import CircuitBreaker
from app.integrations.air_quality.cpcb import CPCBProvider
from app.integrations.air_quality.open_meteo import OpenMeteoProvider
from app.integrations.air_quality.openaq import OpenAQProvider
from app.integrations.geocoding.client import GeocodingClient
from app.integrations.http import create_http_client
from app.services.air_quality_service import ProviderBinding
from app.services.health_service import HealthService
from app.utils.cache import TTLCache

logger = get_logger(__name__)

# psycopg's async connections refuse the Proactor loop Windows selects by
# default, so set the policy before the server creates its loop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = cast(Settings, app.state.settings)
    database = cast(Database, app.state.database)

    logger.info(
        "application_startup",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )
    if database.is_configured:
        if await database.check():
            logger.info("database_ready")
        else:
            logger.warning("database_unavailable_at_startup")
    else:
        logger.warning("database_not_configured")

    try:
        yield
    finally:
        for client_name in (
            "air_client",
            "openaq_client",
            "geocoding_client",
            "ai_client",
        ):
            client = getattr(app.state, client_name, None)
            if client is not None:
                await client.aclose()
        await database.dispose()
        logger.info("application_shutdown")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build an application instance.

    A factory (rather than a module-level app alone) keeps tests independent:
    each test can build an app with its own settings and routes.
    """
    config = settings or get_settings()
    configure_logging(level=config.log_level, json_logs=config.json_logs)

    app = FastAPI(
        title=config.app_name,
        version=config.app_version,
        docs_url="/docs" if config.docs_enabled else None,
        redoc_url=None,
        openapi_url=(
            f"{config.api_v1_prefix}/openapi.json" if config.docs_enabled else None
        ),
        lifespan=lifespan,
    )
    app.state.settings = config
    app.state.database = Database(config)
    app.state.rate_limiter = RateLimiter()
    app.state.air_cache = TTLCache[object](maxsize=512)
    app.state.air_breaker = CircuitBreaker()
    app.state.air_client = create_http_client(
        base_url=config.air_quality_api_base_url,
        timeout_seconds=8.0,
        connect_timeout_seconds=5.0,
    )
    app.state.air_provider = OpenMeteoProvider(app.state.air_client)
    app.state.openaq_breaker = CircuitBreaker()
    app.state.openaq_client = create_http_client(
        base_url=config.openaq_api_base_url,
        timeout_seconds=10.0,
        connect_timeout_seconds=5.0,
    )
    app.state.openaq_provider = OpenAQProvider(
        app.state.openaq_client,
        api_key=(
            config.openaq_api_key.get_secret_value()
            if config.openaq_api_key is not None
            else None
        ),
        station_radius_km=config.openaq_station_radius_km,
        page_size=config.openaq_stations_per_page,
    )
    app.state.cpcb_breaker = CircuitBreaker()
    app.state.cpcb_provider = CPCBProvider(
        enabled=config.cpcb_enabled,
        base_url=config.cpcb_api_base_url,
    )
    app.state.air_bindings = {
        "open-meteo": ProviderBinding(
            provider=app.state.air_provider,
            breaker=app.state.air_breaker,
            budget_key="openmeteo",
            budget=config.openmeteo_daily_call_budget,
        ),
        "openaq": ProviderBinding(
            provider=app.state.openaq_provider,
            breaker=app.state.openaq_breaker,
            budget_key="openaq",
            budget=config.openaq_daily_call_budget,
        ),
        "cpcb": ProviderBinding(
            provider=app.state.cpcb_provider,
            breaker=app.state.cpcb_breaker,
            budget_key="cpcb",
            budget=0,
        ),
    }
    app.state.geocoding_client = GeocodingClient(
        create_http_client(
            base_url=config.geocoding_api_base_url,
            timeout_seconds=8.0,
            connect_timeout_seconds=5.0,
        )
    )
    if config.gemini_api_key is not None:
        app.state.ai_client = create_http_client(
            base_url=config.gemini_api_base_url,
            timeout_seconds=config.ai_request_timeout_seconds,
            connect_timeout_seconds=5.0,
        )
        app.state.gemini = GeminiClient(
            app.state.ai_client,
            api_key=config.gemini_api_key.get_secret_value(),
            model=config.gemini_model,
            timeout_seconds=config.ai_request_timeout_seconds,
        )
    else:
        app.state.ai_client = None
        app.state.gemini = None

    # Added first so it is the innermost middleware.
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.host_allowlist)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=[
            "X-Request-ID",
            "X-Data-Cache",
            "X-Data-Expires-At",
        ],
        max_age=600,
    )
    app.add_middleware(
        BodySizeLimitMiddleware,
        max_bytes=config.request_max_bytes,
    )
    # Added last so every response, including CORS and size rejections, carries
    # a request ID and an access log line.
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)
    app.include_router(api_router, prefix=config.api_v1_prefix)

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", include_in_schema=False)
    async def readyz() -> JSONResponse:
        result = await HealthService(config, cast(Database, app.state.database)).check()
        state = (
            HTTPStatus.OK
            if result.status != "unhealthy"
            else HTTPStatus.SERVICE_UNAVAILABLE
        )
        return JSONResponse(status_code=state, content=result.model_dump(mode="json"))

    return app


app = create_app()
