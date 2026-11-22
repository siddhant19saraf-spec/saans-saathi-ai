"""Anonymous session lifecycle and privacy operations."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import hash_token, issue_token
from app.models.profile import Profile
from app.repositories import (
    conversations,
    households,
    impact,
    profiles as profiles_repo,
)
from app.schemas.sessions import (
    ConsentState,
    SessionCreate,
    SessionCreated,
    SessionInfo,
)
from app.utils.time import utc_now


async def create(
    session: AsyncSession, settings: Settings, payload: SessionCreate
) -> SessionCreated:
    now = utc_now()
    expires_at = now + settings.session_ttl
    token = issue_token()
    profile = await profiles_repo.create(
        session,
        token_hash=hash_token(token),
        consent_version=payload.consent_version,
        health_consent_at=now if payload.health_consent else None,
        expires_at=expires_at,
    )
    await impact.log_privacy_event(
        session,
        profile_id=profile.id,
        event="consent",
        meta={
            "consent_version": payload.consent_version,
            "health_consent": payload.health_consent,
        },
    )
    await session.commit()
    return SessionCreated(
        token=token, expires_at=profile.expires_at, profile_id=profile.id
    )


async def info(session: AsyncSession, profile: Profile) -> SessionInfo:
    household = await households.get_for_profile(session, profile.id)
    return SessionInfo(
        profile_id=profile.id,
        has_household=household is not None,
        consent=ConsentState(
            version=profile.consent_version,
            health_consent_at=profile.health_consent_at,
        ),
        expires_at=profile.expires_at,
    )


async def grant_health_consent(
    session: AsyncSession, profile: Profile, *, health_consent: bool
) -> SessionInfo:
    if health_consent and profile.health_consent_at is None:
        profile.health_consent_at = utc_now()
    await impact.log_privacy_event(
        session,
        profile_id=profile.id,
        event="consent",
        meta={"health_consent": health_consent},
    )
    await session.commit()
    return await info(session, profile)


async def delete_all(session: AsyncSession, profile: Profile) -> None:
    profile_id = profile.id
    await conversations.delete_conversations_for_profile(session, profile_id)
    await impact.delete_activities_for_profile(session, profile_id)
    await impact.log_privacy_event(
        session, profile_id=profile_id, event="delete_all", meta={}
    )
    await profiles_repo.delete(session, profile)
    await session.commit()
