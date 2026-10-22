"""Persist connection settings (origin + optional secret) as a single use-case.

Lives in the services layer so the UI never imports the secret store and cannot hold
Fernet objects. Returns a small outcome carrying a ``ru`` error key on failure.

The same functions serve the two UI paths that write the store: saving the connection
dialog and remembering the secret after a successful login.
"""

from __future__ import annotations

from dataclasses import dataclass

from market_monitor_gui.config.config_store import ConfigStore
from market_monitor_gui.config.secret_store import SecretStore, SecretStoreError


@dataclass(frozen=True, slots=True)
class SaveOutcome:
    """Result of a connection/secret write."""

    ok: bool
    error_key: str | None


def save_connection(
    config: ConfigStore,
    secrets: SecretStore,
    *,
    origin: str,
    secret: str | None,
    save_secret: bool,
    clear_secret: bool = False,
) -> SaveOutcome:
    """Persist the origin and the secret according to the operator's checkbox.

    ``clear_secret`` (the checkbox left off) deletes the stored secret; otherwise
    ``save_secret`` with a non-empty ``secret`` stores it, and an empty field keeps the
    existing one untouched.
    """
    try:
        config.save_api_base_url(origin)
        if clear_secret:
            secrets.clear()
        elif save_secret and secret:
            secrets.save(secret)
    except SecretStoreError:
        return SaveOutcome(ok=False, error_key="ERR_SECRET_SAVE")
    except OSError, ValueError:
        return SaveOutcome(ok=False, error_key="ERR_UNEXPECTED")
    return SaveOutcome(ok=True, error_key=None)


def store_secret(secrets: SecretStore, secret: str) -> SaveOutcome:
    """Store ``secret`` after a successful login (the login dialog's checkbox)."""
    try:
        secrets.save(secret)
    except SecretStoreError:
        return SaveOutcome(ok=False, error_key="ERR_SECRET_SAVE")
    except OSError, ValueError:
        return SaveOutcome(ok=False, error_key="ERR_UNEXPECTED")
    return SaveOutcome(ok=True, error_key=None)


def forget_secret(secrets: SecretStore) -> SaveOutcome:
    """Delete the stored secret without touching the current session."""
    secrets.clear()
    return SaveOutcome(ok=True, error_key=None)
