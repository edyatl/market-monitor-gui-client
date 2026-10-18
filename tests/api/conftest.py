"""Fixtures and helpers for API-layer tests."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from typing import Protocol

import httpx
import pytest

from market_monitor_gui.api.client import ApiClient
from market_monitor_gui.api.transport import build_client

Handler = Callable[[httpx.Request], httpx.Response]

DEFAULT_ORIGIN = "https://api.test.example"


class MakeClient(Protocol):
    """Factory that builds an :class:`ApiClient` around a mock handler."""

    def __call__(self, handler: Handler) -> ApiClient: ...


class RecordingApiClient(ApiClient):
    """An :class:`ApiClient` that keeps the requests it issued for assertions."""

    def __init__(self, client: httpx.Client, *, origin: str, seen: list[httpx.Request]) -> None:
        super().__init__(client, origin=origin)
        self.requests_seen = seen


@pytest.fixture
def make_client() -> Iterator[MakeClient]:
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


def recording_client(origin: str, handler: Handler) -> RecordingApiClient:
    """Build a :class:`RecordingApiClient` over a fresh ``MockTransport``."""
    seen, wrapped = record_requests(handler)
    underlying = build_client(origin, transport=httpx.MockTransport(wrapped))
    return RecordingApiClient(underlying, origin=origin, seen=seen)


def record_requests(handler: Handler) -> tuple[list[httpx.Request], Handler]:
    """Wrap ``handler`` to record every request it receives."""
    seen: list[httpx.Request] = []

    def wrapped(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    return seen, wrapped


def urls(requests: Sequence[httpx.Request]) -> list[str]:
    return [str(request.url) for request in requests]
