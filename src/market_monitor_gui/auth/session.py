"""Session lifecycle: login, coordinated one-shot re-login on 401, disconnect.

Rules enforced here (see AGENTS.md):

- the session cookie is the credential; the secret is used only to log in;
- on ``401`` a **read** may trigger exactly one coordinated re-login and then retry
  the read once — never a loop;
- a **write** is never retried or replayed after ``401``: the caller refreshes and
  shows server state;
- re-login is single-flight: concurrent ``401`` readers share one login.

Disconnecting (``disconnect()``) ends the session only; a stored secret is kept.

Thread-safe and free of any UI imports; the status bar observes state via the
``on_state_change`` callback.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from enum import StrEnum
from typing import TypeVar

from market_monitor_gui.api.client import ApiClient
from market_monitor_gui.api.errors import ApiError, ErrorKind

_T = TypeVar("_T")


class SessionState(StrEnum):
    """Observable session state for the status bar."""

    SIGNED_OUT = "signed_out"
    SIGNED_IN = "signed_in"
    EXPIRED = "expired"


class AuthRequiredError(ApiError):
    """Raised when a call needs authentication that cannot be (re)established."""

    def __init__(
        self,
        text_key: str,
        *,
        method: str | None = None,
        path: str | None = None,
    ) -> None:
        super().__init__(ErrorKind.UNAUTHORIZED, text_key=text_key, method=method, path=path)


class SessionManager:
    """Own the authenticated session for one :class:`ApiClient`."""

    def __init__(
        self,
        api: ApiClient,
        *,
        secret_provider: Callable[[], str | None],
        on_state_change: Callable[[SessionState], None] | None = None,
    ) -> None:
        self._api = api
        self._secret_provider = secret_provider
        self._on_state_change = on_state_change
        self._lock = threading.Lock()
        self._epoch = 0
        self._state = SessionState.SIGNED_OUT
        self._expires_in: int | None = None

    @property
    def state(self) -> SessionState:
        return self._state

    @property
    def session_expires_in(self) -> int | None:
        """Seconds reported by the last successful login, or ``None``."""
        return self._expires_in

    def login(self, secret: str | None = None) -> SessionState:
        """Log in explicitly, using ``secret`` or the resolver's secret.

        Raises:
            AuthRequiredError: when no secret is available.
            ApiError: when the server rejects the secret.
        """
        value = secret if secret is not None else self._secret_provider()
        if not value:
            self._set_state(SessionState.SIGNED_OUT)
            raise AuthRequiredError("ERR_SECRET_REQUIRED")
        self._authenticate(value)
        return self._state

    def ensure_session(self) -> None:
        """Log in if there is currently no usable session."""
        if self._state is SessionState.SIGNED_IN and self._api.has_session_cookies():
            return
        self.login()

    def check_session(self) -> bool:
        """Validate the current cookie against the server. Never re-logs in."""
        if not self._api.has_session_cookies():
            self._set_state(SessionState.SIGNED_OUT)
            return False
        try:
            result = self._api.check_auth()
        except ApiError as exc:
            if exc.kind is ErrorKind.UNAUTHORIZED:
                self._set_state(SessionState.EXPIRED)
                return False
            raise
        if result.authenticated:
            self._set_state(SessionState.SIGNED_IN)
            return True
        self._set_state(SessionState.EXPIRED)
        return False

    def read(self, fn: Callable[[], _T]) -> _T:
        """Run a safe GET-style call, retrying once after a coordinated re-login."""
        return self._call(fn, allow_relogin=True)

    def write(self, fn: Callable[[], _T]) -> _T:
        """Run a mutating call. Never re-logged in or replayed automatically."""
        return self._call(fn, allow_relogin=False)

    def disconnect(self) -> None:
        """End the session (clear the cookies and reset state) but keep any stored secret.

        The operator-facing disconnect action maps here: the session cookie is dropped,
        while the encrypted secret on disk is untouched so the next sign-in needs no typing.
        """
        self._api.clear_session_cookies()
        self._expires_in = None
        with self._lock:
            self._epoch += 1
        self._set_state(SessionState.SIGNED_OUT)

    # -- internals ------------------------------------------------------------

    def _call(self, fn: Callable[[], _T], *, allow_relogin: bool) -> _T:
        epoch = self._epoch
        try:
            return fn()
        except ApiError as exc:
            if exc.kind is not ErrorKind.UNAUTHORIZED:
                raise
            if not allow_relogin:
                self._set_state(SessionState.EXPIRED)
                raise

            secret = self._secret_provider()
            if not secret:
                self._set_state(SessionState.EXPIRED)
                raise AuthRequiredError(
                    "ERR_SESSION_EXPIRED", method=exc.method, path=exc.path
                ) from exc

            self._relogin(epoch, secret)
            try:
                return fn()
            except ApiError as retry_exc:
                if retry_exc.kind is ErrorKind.UNAUTHORIZED:
                    self._set_state(SessionState.EXPIRED)
                    raise AuthRequiredError(
                        "ERR_SESSION_EXPIRED",
                        method=retry_exc.method,
                        path=retry_exc.path,
                    ) from retry_exc
                raise

    def _authenticate(self, secret: str) -> None:
        """Perform an operator-initiated login and update state."""
        try:
            response = self._api.login(secret)
        except ApiError:
            self._fail_login()
            raise
        self._expires_in = response.expires_in
        with self._lock:
            self._epoch += 1
        self._set_state(SessionState.SIGNED_IN)

    def _relogin(self, epoch: int, secret: str) -> bool:
        """Re-login once, single-flight across threads.

        Returns True when this call performed the login, False when another thread
        already refreshed the session.
        """
        with self._lock:
            if self._epoch != epoch:
                return False
            try:
                response = self._api.login(secret)
            except ApiError:
                self._api.clear_session_cookies()
                self._expires_in = None
                self._state = SessionState.SIGNED_OUT
                self._notify()
                raise
            self._expires_in = response.expires_in
            self._epoch = epoch + 1
        self._set_state(SessionState.SIGNED_IN)
        return True

    def _fail_login(self) -> None:
        self._api.clear_session_cookies()
        self._expires_in = None
        self._set_state(SessionState.SIGNED_OUT)

    def _set_state(self, state: SessionState) -> None:
        with self._lock:
            if self._state is state:
                return
            self._state = state
        self._notify()

    def _notify(self) -> None:
        if self._on_state_change is not None:
            self._on_state_change(self._state)
