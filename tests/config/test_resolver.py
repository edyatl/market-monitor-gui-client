"""G19: secret-presence helpers used by the connection/login UI (Tk-free)."""

from __future__ import annotations

from pathlib import Path

import pytest

from market_monitor_gui.config.resolver import SecretResolver
from market_monitor_gui.config.secret_store import SecretStore
from market_monitor_gui.config.settings import AppSettings

pytestmark = pytest.mark.unit


def _resolver(tmp_path: Path) -> SecretResolver:
    return SecretResolver(SecretStore(tmp_path), AppSettings(_env_file=None))


def test_presence_is_false_without_any_secret(tmp_path: Path) -> None:
    resolver = _resolver(tmp_path)
    assert resolver.has_stored_secret() is False
    assert resolver.has_env_secret() is False
    assert resolver.has_secret() is False


def test_presence_reports_a_stored_secret(tmp_path: Path) -> None:
    store = SecretStore(tmp_path)
    store.save("dummy")
    resolver = _resolver(tmp_path)
    assert resolver.has_stored_secret() is True
    assert resolver.has_env_secret() is False
    assert resolver.has_secret() is True


def test_presence_reports_the_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_SECRET", "env-secret")
    resolver = _resolver(tmp_path)
    assert resolver.has_stored_secret() is False
    assert resolver.has_env_secret() is True
    assert resolver.has_secret() is True


def test_blank_env_override_is_not_a_secret(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APP_SECRET", "")
    resolver = _resolver(tmp_path)
    assert resolver.has_env_secret() is False
    assert resolver.has_secret() is False
