"""G5: session login, coordinated re-login, and logout."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable, Iterator
from typing import Any

import httpx
import pytest

from market_monitor_gui.api.client import ApiClient
from market_monitor_gui.api.dto import GroupResponse, SettingsPatchRequest
from market_monitor_gui.api.errors import ApiError, ErrorKind
from market_monitor_gui.auth.session import AuthRequiredError, SessionManager, SessionState

pytestmark = pytest.mark.unit

ORIGIN = "https://api.test.example"
SECRET = "correct-secret"
GROUP = {
    "id": 1,
    "name": "g",
    "url": "https://m/x",
    "enabled": True,
    "sort_order": 0,
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-01T00:00:00",
}
UNAUTHORIZED = {
    "type": "about:blank",
    "title": "Unauthorized",
    "status": 401,
    "detail": "Authentication required",
}


class FakeServer:
    """Minimal stateful stand-in for the control-plane auth + a couple of routes."""

    def __init__(self, *, reject_after_login: bool = False) -> None:
        self.login_calls = 0
        self.protected_calls = 0
        self.patch_calls = 0
        self.login_delay = 0.0
        self._tokens: set[str] = set()
        self._seq = 0
        self._reject_after_login = reject_after_login

    def invalidate_all(self) -> None:
        self._tokens.clear()

    def _token(self, request: httpx.Request) -> str | None:
        for part in request.headers.get("cookie", "").split(";"):
            part = part.strip()
            if part.startswith("gui_session="):
                return part.split("=", 1)[1]
        return None

    def _authorized(self, request: httpx.Request) -> bool:
        if self._reject_after_login:
            return False
        token = self._token(request)
        return token is not None and token in self._tokens

    def handler(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/auth/app-login"):
            self.login_calls += 1
            if self.login_delay:
                time.sleep(self.login_delay)
            body = json.loads(request.content)
            if body.get("client_secret") != SECRET:
                return httpx.Response(401, json=UNAUTHORIZED)
            self._seq += 1
            token = f"tok{self._seq}"
            self._tokens.add(token)
            return httpx.Response(
                200,
                json={"authenticated": True, "expires_in": 3600},
                headers={"set-cookie": f"gui_session={token}; Path=/"},
            )
        if path.endswith("/auth/check") and request.method == "GET":
            self.protected_calls += 1
            if self._authorized(request):
                return httpx.Response(200, json={"authenticated": True})
            return httpx.Response(401, json=UNAUTHORIZED)
        if path.endswith("/groups") and request.method == "GET":
            self.protected_calls += 1
            if self._authorized(request):
                return httpx.Response(200, json=[GROUP])
            return httpx.Response(401, json=UNAUTHORIZED)
        if path.endswith("/settings") and request.method == "PATCH":
            self.patch_calls += 1
            if self._authorized(request):
                return httpx.Response(200, json={"price_drop_threshold_percent": 5.0})
            return httpx.Response(401, json=UNAUTHORIZED)
        return httpx.Response(404, json={"detail": "unhandled"})


class Harness:
    def __init__(self, server: FakeServer, secret: str | None = SECRET) -> None:
        self.server = server
        self.api = ApiClient.create(ORIGIN, transport=httpx.MockTransport(server.handler))
        self._secret = secret
        self.states: list[SessionState] = []
        self.manager = SessionManager(
            self.api,
            secret_provider=self._provide,
            on_state_change=self.states.append,
        )

    def _provide(self) -> str | None:
        return self._secret

    def set_secret(self, secret: str | None) -> None:
        self._secret = secret

    def close(self) -> None:
        self.api.close()


@pytest.fixture
def make_harness() -> Iterator[Callable[..., Harness]]:
    created: list[Harness] = []

    def _make(*, secret: str | None = SECRET, reject_after_login: bool = False) -> Harness:
        harness = Harness(FakeServer(reject_after_login=reject_after_login), secret)
        created.append(harness)
        return harness

    yield _make

    for harness in created:
        harness.close()


def test_login_success(make_harness: Callable[..., Harness]) -> None:
    harness = make_harness()
    assert harness.manager.login() is SessionState.SIGNED_IN
    assert harness.manager.state is SessionState.SIGNED_IN
    assert harness.manager.session_expires_in == 3600
    assert harness.api.has_session_cookies() is True
    assert harness.states == [SessionState.SIGNED_IN]


def test_login_with_explicit_secret(make_harness: Callable[..., Harness]) -> None:
    harness = make_harness(secret=None)
    harness.set_secret(None)
    assert harness.manager.login("correct-secret") is SessionState.SIGNED_IN


def test_login_wrong_secret(make_harness: Callable[..., Harness]) -> None:
    harness = make_harness()
    with pytest.raises(ApiError) as excinfo:
        harness.manager.login("wrong-secret")
    assert excinfo.value.kind is ErrorKind.UNAUTHORIZED
    assert harness.manager.state is SessionState.SIGNED_OUT
    assert harness.api.has_session_cookies() is False


def test_login_without_any_secret(make_harness: Callable[..., Harness]) -> None:
    harness = make_harness(secret=None)
    with pytest.raises(AuthRequiredError) as excinfo:
        harness.manager.login()
    assert excinfo.value.text_key == "ERR_SECRET_REQUIRED"
    assert harness.server.login_calls == 0


def test_check_session_without_cookie(make_harness: Callable[..., Harness]) -> None:
    harness = make_harness()
    assert harness.manager.check_session() is False
    assert harness.manager.state is SessionState.SIGNED_OUT
    assert harness.server.protected_calls == 0


def test_check_session_valid(make_harness: Callable[..., Harness]) -> None:
    harness = make_harness()
    harness.manager.login()
    assert harness.manager.check_session() is True
    assert harness.manager.state is SessionState.SIGNED_IN


def test_check_session_expired(make_harness: Callable[..., Harness]) -> None:
    harness = make_harness()
    harness.manager.login()
    harness.server.invalidate_all()
    assert harness.manager.check_session() is False
    assert harness.manager.state is SessionState.EXPIRED
    assert harness.server.login_calls == 1


def test_read_relogins_once_and_retries(make_harness: Callable[..., Harness]) -> None:
    harness = make_harness()
    harness.manager.login()
    harness.server.invalidate_all()

    groups = harness.manager.read(lambda: harness.api.list_groups())

    assert [group.id for group in groups] == [1]
    assert harness.server.login_calls == 2
    assert harness.server.protected_calls == 2
    assert harness.manager.state is SessionState.SIGNED_IN


def test_read_does_not_loop_when_relogin_does_not_help(
    make_harness: Callable[..., Harness],
) -> None:
    harness = make_harness(reject_after_login=True)
    harness.manager.login()

    with pytest.raises(AuthRequiredError) as excinfo:
        harness.manager.read(lambda: harness.api.list_groups())

    assert excinfo.value.text_key == "ERR_SESSION_EXPIRED"
    assert harness.server.login_calls == 2  # initial login + exactly one re-login
    assert harness.manager.state is SessionState.EXPIRED


def test_write_is_never_replayed(make_harness: Callable[..., Harness]) -> None:
    harness = make_harness()
    harness.manager.login()
    harness.server.invalidate_all()

    with pytest.raises(ApiError) as excinfo:
        harness.manager.write(
            lambda: harness.api.patch_settings(
                SettingsPatchRequest(price_drop_threshold_percent=5.0)
            )
        )

    assert excinfo.value.kind is ErrorKind.UNAUTHORIZED
    assert harness.server.login_calls == 1  # no re-login for writes
    assert harness.server.patch_calls == 1  # no replay
    assert harness.manager.state is SessionState.EXPIRED


def test_read_without_secret_raises_auth_required(
    make_harness: Callable[..., Harness],
) -> None:
    harness = make_harness(secret=None)
    harness.set_secret(None)
    with pytest.raises(AuthRequiredError) as excinfo:
        harness.manager.read(lambda: harness.api.list_groups())
    assert excinfo.value.text_key == "ERR_SESSION_EXPIRED"
    assert harness.server.login_calls == 0
    assert harness.manager.state is SessionState.EXPIRED


def test_ensure_session_logs_in_from_resolver(make_harness: Callable[..., Harness]) -> None:
    harness = make_harness()
    harness.manager.ensure_session()
    assert harness.manager.state is SessionState.SIGNED_IN
    assert harness.server.login_calls == 1
    harness.manager.ensure_session()  # idempotent
    assert harness.server.login_calls == 1


def test_logout_clears_session(make_harness: Callable[..., Harness]) -> None:
    harness = make_harness()
    harness.manager.login()
    harness.manager.logout()
    assert harness.manager.state is SessionState.SIGNED_OUT
    assert harness.api.has_session_cookies() is False
    assert harness.manager.session_expires_in is None


def test_non_auth_errors_are_not_retried(make_harness: Callable[..., Harness]) -> None:
    harness = make_harness()
    harness.manager.login()

    def boom() -> list[Any]:
        raise ApiError(ErrorKind.SERVER)

    with pytest.raises(ApiError) as excinfo:
        harness.manager.read(boom)
    assert excinfo.value.kind is ErrorKind.SERVER
    assert harness.server.login_calls == 1


def test_concurrent_reads_share_one_relogin(make_harness: Callable[..., Harness]) -> None:
    harness = make_harness()
    harness.server.login_delay = 0.05
    harness.manager.login()
    harness.server.invalidate_all()

    barrier = threading.Barrier(2)
    errors: list[BaseException] = []
    results: list[list[GroupResponse]] = []

    def worker() -> None:
        try:
            barrier.wait(timeout=5)
            results.append(harness.manager.read(lambda: harness.api.list_groups()))
        except BaseException as exc:  # surfaced via the assertion below
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert not errors, errors
    assert len(results) == 2
    # initial login + exactly one coordinated re-login
    assert harness.server.login_calls == 2
