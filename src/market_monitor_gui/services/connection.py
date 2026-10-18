"""Persist connection settings (origin + optional secret) as a single use-case.

Lives in the services layer so the UI never imports the secret store and cannot hold
Fernet objects. Returns a small outcome carrying a ``ru`` error key on failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from market_monitor_gui.config.config_store import ConfigStore
from market_monitor_gui.config.secret_store import SecretStore, SecretStoreError
from market_monitor_gui.texts import ru


@dataclass(frozen=True, slots=True)
class SaveOutcome:
    """Result of saving connection settings."""

    ok: bool
    error_key: str | None


def save_connection(
    config: ConfigStore,
    secrets: SecretStore,
    *,
    origin: str,
    secret: str | None,
    save_secret: bool,
) -> SaveOutcome:
    """Persist the origin and, when requested, the encrypted secret."""
    try:
        config.save_api_base_url(origin)
        if save_secret and secret:
            secrets.save(secret)
    except SecretStoreError:
        return SaveOutcome(ok=False, error_key=ru.ERR_SECRET_SAVE)
    except OSError, ValueError:
        return SaveOutcome(ok=False, error_key=ru.ERR_UNEXPECTED)
    return SaveOutcome(ok=True, error_key=None)
