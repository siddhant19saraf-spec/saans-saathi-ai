"""Anonymous profile persistence."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile, utc_now


async def get_by_token_hash(
    session: AsyncSession,
    token_hash: bytes,
) -> Profile | None:
    statement = select(Profile).where(
        Profile.token_hash == token_hash,
        Profile.deleted_at.is_(None),
        Profile.expires_at > utc_now(),
    )
    return await session.scalar(statement)


async def get_by_id(session: AsyncSession, profile_id: UUID) -> Profile | None:
    statement = select(Profile).where(
        Profile.id == profile_id,
        Profile.deleted_at.is_(None),
    )
    return await session.scalar(statement)


async def create(
    session: AsyncSession,
    *,
    token_hash: bytes,
    consent_version: str,
    health_consent_at: datetime | None,
    expires_at: datetime,
) -> Profile:
    profile = Profile(
        token_hash=token_hash,
        consent_version=consent_version,
        health_consent_at=health_consent_at,
        expires_at=expires_at,
    )
    session.add(profile)
    await session.flush()
    return profile


async def touch(session: AsyncSession, profile: Profile) -> None:
    profile.last_seen_at = utc_now()
    await session.flush()


async def delete(session: AsyncSession, profile: Profile) -> None:
    await session.delete(profile)
    await session.flush()
