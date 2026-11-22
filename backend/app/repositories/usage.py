"""Daily usage counters shared by provider and AI budgets."""

from __future__ import annotations

from datetime import date

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.impact import UsageDaily


async def record_tokens(
    session: AsyncSession,
    *,
    key: str,
    day: date,
    input_tokens: int | None,
    output_tokens: int | None,
) -> None:
    statement = pg_insert(UsageDaily).values(
        day=day,
        key=key,
        requests=0,
        input_tokens=input_tokens or 0,
        output_tokens=output_tokens or 0,
    )
    statement = statement.on_conflict_do_update(
        index_elements=[UsageDaily.day, UsageDaily.key],
        set_={
            "input_tokens": UsageDaily.input_tokens + (input_tokens or 0),
            "output_tokens": UsageDaily.output_tokens + (output_tokens or 0),
        },
    )
    await session.execute(statement)
