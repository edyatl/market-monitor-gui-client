"""Fixtures for API-layer tests."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence

import httpx
import pytest

from market_monitor_gui.api.client import ApiClient

Handler = Callable[[httpx.Request], httpx.Response]

DEFAULT_ORIGIN = "https://api.test.example"


@pytest.fixture
def make_client() -> Iterator[Callable[..., ApiClient]]:
    """Return a factory building an :class:`ApiClient` over a ``MockTransport``."""
    created: list[ApiClient] = []

    def _make(
        handler: Handler,
        *,
        origin: str = DEFAULT_ORIGIN,
        transport: httpx.BaseTransport | None = None,
    ) -> ApiClient:
        client = ApiClient.create(
            origin,
            transport=transport if transport is not None else httpx.MockTransport(handler),
        )
        created.append(client)
        return client

    yield _make

    for client in created:
        client.close()


def record_requests(handler: Handler) -> tuple[list[httpx.Request], Handler]:
    """Wrap ``handler`` to record every request it receives."""
    seen: list[httpx.Request] = []

    def wrapped(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    return seen, wrapped


def urls(requests: Sequence[httpx.Request]) -> list[str]:
    return [str(request.url) for request in requests]
