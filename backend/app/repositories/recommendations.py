"""Generated advice retrieval and lifecycle."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.routine import Recommendation


async def create(
    session: AsyncSession,
    *,
    household_id: UUID,
    module: str,
    severity: str,
    title: str,
    body: str,
    source: str,
    fact_refs: list[str] | None = None,
    routine_id: UUID | None = None,
    model: str | None = None,
    valid_until: datetime | None = None,
    rule_id: str | None = None,
    payload: dict[str, object] | None = None,
) -> Recommendation:
    recommendation = Recommendation(
        household_id=household_id,
        routine_id=routine_id,
        module=module,
        severity=severity,
        title=title,
        body=body,
        fact_refs=fact_refs or [],
        rule_id=rule_id,
        payload=payload or {},
        source=source,
        model=model,
        valid_until=valid_until,
    )
    session.add(recommendation)
    await session.flush()
    return recommendation


async def get(
    session: AsyncSession, *, household_id: UUID, recommendation_id: UUID
) -> Recommendation | None:
    return await session.scalar(
        select(Recommendation).where(
            Recommendation.id == recommendation_id,
            Recommendation.household_id == household_id,
        )
    )


async def list_for_household(
    session: AsyncSession,
    *,
    household_id: UUID,
    limit: int,
    offset: int = 0,
    module: str | None = None,
    include_dismissed: bool = False,
) -> list[Recommendation]:
    statement = select(Recommendation).where(
        Recommendation.household_id == household_id
    )
    if module is not None:
        statement = statement.where(Recommendation.module == module)
    if not include_dismissed:
        statement = statement.where(Recommendation.dismissed_at.is_(None))
    statement = (
        statement.order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list((await session.scalars(statement)).all())


async def dismiss(
    session: AsyncSession, recommendation: Recommendation, *, now: datetime
) -> Recommendation:
    recommendation.dismissed_at = now
    await session.flush()
    return recommendation


async def delete(session: AsyncSession, recommendation: Recommendation) -> None:
    await session.delete(recommendation)
    await session.flush()
