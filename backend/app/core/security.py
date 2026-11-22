"""Opaque session tokens and transport-level authentication helpers.

Sessions are anonymous device identities. The raw token is returned exactly
once and only its SHA-256 digest is persisted, so a database leak does not
yield usable bearer tokens.
"""

from __future__ import annotations

import hashlib
import secrets

TOKEN_BYTES = 32
_BEARER_PREFIX = "bearer "


def issue_token() -> str:
    """Return a URL-safe opaque token with 256 bits of entropy."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> bytes:
    return hashlib.sha256(token.encode("utf-8")).digest()


def parse_bearer(header_value: str | None) -> str | None:
    """Extract a token from an ``Authorization`` header.

    Returns ``None`` for missing or malformed headers so the caller decides
    whether authentication is required or optional.
    """
    if not header_value:
        return None
    candidate = header_value.strip()
    if not candidate.lower().startswith(_BEARER_PREFIX):
        return None
    token = candidate[len(_BEARER_PREFIX) :].strip()
    if not token or len(token) > 256:
        return None
    return token
