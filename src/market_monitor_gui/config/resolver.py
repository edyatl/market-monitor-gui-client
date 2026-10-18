"""Resolve which shared secret to use for login / re-login.

Resolution order for automatic login, matching the documented behaviour:

1. the environment / ``.env`` override (``APP_SECRET``, or legacy ``API_APP_KEY``);
2. the encrypted secret store.

A secret typed in the login dialog is not resolved here: it is passed straight to
:meth:`market_monitor_gui.auth.session.SessionManager.login` and used for that call
only (and may then be saved to the store by the operator).
"""

from __future__ import annotations

from market_monitor_gui.config.secret_store import SecretStore
from market_monitor_gui.config.settings import AppSettings


class SecretResolver:
    """Combine the environment override with the encrypted secret store."""

    def __init__(self, store: SecretStore, settings: AppSettings | None = None) -> None:
        self._store = store
        self._settings = settings if settings is not None else AppSettings()

    def resolve(self) -> str | None:
        """Return the secret to log in with, or ``None`` when none is available."""
        if self._settings.app_secret is not None:
            value = self._settings.app_secret.get_secret_value()
            if value:
                return value
        return self._store.load()
