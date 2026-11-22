"""Shared daily budget gate for paid model calls."""

from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.logging import get_logger
from app.repositories import air as air_repo
from app.utils.time import utc_now

logger = get_logger(__name__)

AI_BUDGET_KEY = "gemini"


async def ai_budget_allows(session: AsyncSession | None, settings: Settings) -> bool:
    if settings.gemini_api_key is None:
        return False
    if session is None:
        return True
    try:
        allowed = await air_repo.consume_budget(
            session,
            key=AI_BUDGET_KEY,
            budget=settings.ai_daily_request_budget,
            day=utc_now().date(),
        )
        await session.commit()
        return allowed
    except SQLAlchemyError:
        await session.rollback()
        logger.warning("ai_budget_check_failed")
        return False
