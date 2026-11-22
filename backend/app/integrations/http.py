"""HTTP client foundation for external providers.

Providers get a pre-configured client with bounded timeouts, a connection pool
and redirects disabled. No external call is made in this milestone.
"""

from __future__ import annotations

import httpx


def create_http_client(
    *,
    base_url: str,
    timeout_seconds: float = 8.0,
    connect_timeout_seconds: float = 5.0,
    max_connections: int = 50,
) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=base_url,
        timeout=httpx.Timeout(timeout_seconds, connect=connect_timeout_seconds),
        limits=httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=10,
        ),
        headers={"User-Agent": "saans-saathi-api/0.1.0"},
        follow_redirects=False,
    )
