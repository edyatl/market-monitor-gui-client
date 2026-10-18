"""G4: login flow, cookie handling, and auth requests."""

from __future__ import annotations

import json

import httpx
import pytest

from market_monitor_gui.api.client import ApiClient
from market_monitor_gui.api.errors import ApiError, ErrorKind

from .conftest import DEFAULT_ORIGIN, record_requests, urls

pytestmark = pytest.mark.unit

LOGIN_BODY = {"authenticated": True, "expires_in": 3600}
COOKIE_HEADER = {"set-cookie": "gui_session=test-token; Path=/; HttpOnly"}


def test_login_posts_secret_and_path(make_client) -> None:
    seen, handler = record_requests(
        lambda request: httpx.Response(200, json=LOGIN_BODY, headers=COOKIE_HEADER)
    )
    client = make_client(handler)

    response = client.login("s3cret")

    assert response.authenticated is True
    assert response.expires_in == 3600
    assert urls(seen) == [f"{DEFAULT_ORIGIN}/api/v1/auth/app-login"]
    assert seen[0].method == "POST"
    assert json.loads(seen[0].content) == {"client_secret": "s3cret"}


def test_login_stores_session_cookie_and_protected_call_sends_it(make_client) -> None:
    seen, handler = record_requests(
        lambda request: httpx.Response(
            200,
            json=LOGIN_BODY if request.url.path.endswith("app-login") else {"authenticated": True},
            headers=COOKIE_HEADER if request.url.path.endswith("app-login") else {},
        )
    )
    client = make_client(handler)

    assert client.has_session_cookies() is False
    client.login("s3cret")
    assert client.has_session_cookies() is True
    client.check_auth()

    assert seen[0].headers.get("cookie") is None
    assert "gui_session=test-token" in seen[1].headers.get("cookie", "")


def test_never_sends_x_app_key(make_client) -> None:
    seen, handler = record_requests(
        lambda request: httpx.Response(200, json=LOGIN_BODY, headers=COOKIE_HEADER)
    )
    client = make_client(handler)
    client.login("s3cret")
    client.check_auth()
    for request in seen:
        assert "x-app-key" not in request.headers


def test_logout_clears_cookies(make_client) -> None:
    _, handler = record_requests(
        lambda request: httpx.Response(200, json=LOGIN_BODY, headers=COOKIE_HEADER)
    )
    client = make_client(handler)
    client.login("s3cret")
    client.clear_session_cookies()
    assert client.has_session_cookies() is False


def test_unauthorized_login_raises_without_storing_cookie(make_client) -> None:
    handler = lambda request: httpx.Response(  # noqa: E731
        401,
        json={
            "type": "about:blank",
            "title": "Unauthorized",
            "status": 401,
            "detail": "Authentication required",
            "instance": "/api/v1/auth/app-login",
        },
        headers={"content-type": "application/problem+json"},
    )
    client = make_client(handler)
    with pytest.raises(ApiError) as excinfo:
        client.login("wrong")
    assert excinfo.value.kind is ErrorKind.UNAUTHORIZED
    assert excinfo.value.status_code == 401
    assert client.has_session_cookies() is False


def test_check_auth_false(make_client) -> None:
    client = make_client(lambda request: httpx.Response(200, json={"authenticated": False}))
    assert client.check_auth().authenticated is False


def test_origin_is_exposed(make_client) -> None:
    client = make_client(lambda request: httpx.Response(200, json=LOGIN_BODY))
    assert client.origin == DEFAULT_ORIGIN


def test_api_client_create_returns_typed_client() -> None:
    client = ApiClient.create(
        DEFAULT_ORIGIN, transport=httpx.MockTransport(lambda request: httpx.Response(200))
    )
    try:
        assert isinstance(client, ApiClient)
    finally:
        client.close()
