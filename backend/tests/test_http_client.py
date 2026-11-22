from __future__ import annotations

from app.integrations.http import create_http_client


async def test_http_client_is_bounded_and_does_not_follow_redirects() -> None:
    async with create_http_client(
        base_url="https://example.com",
        timeout_seconds=8.0,
    ) as client:
        assert client.timeout.read == 8.0
        assert client.timeout.connect == 5.0
        assert client.follow_redirects is False
        assert client.headers["user-agent"].startswith("saans-saathi-api/")
