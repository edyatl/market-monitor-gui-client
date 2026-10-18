"""G3: environment/.env settings and secret resolution precedence."""

from __future__ import annotations

from pathlib import Path

import pytest

from market_monitor_gui.config.resolver import SecretResolver
from market_monitor_gui.config.secret_store import SecretStore
from market_monitor_gui.config.settings import AppSettings
from market_monitor_gui.config.urls import DEFAULT_API_BASE_URL

pytestmark = pytest.mark.unit


def test_defaults() -> None:
    settings = AppSettings(_env_file=None)
    assert settings.api_base_url == DEFAULT_API_BASE_URL
    assert settings.app_secret is None
    assert settings.app_env == "production"


def test_api_base_url_from_env_is_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_BASE_URL", "http://localhost:8000/api/v1/")
    assert AppSettings(_env_file=None).api_base_url == "http://localhost:8000"


def test_app_secret_from_env_is_masked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_SECRET", "super-secret")
    settings = AppSettings(_env_file=None)
    assert settings.app_secret is not None
    assert settings.app_secret.get_secret_value() == "super-secret"
    assert "super-secret" not in str(settings)
    assert "super-secret" not in repr(settings)


def test_legacy_api_app_key_is_a_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_APP_KEY", "legacy-secret")
    settings = AppSettings(_env_file=None)
    assert settings.app_secret is not None
    assert settings.app_secret.get_secret_value() == "legacy-secret"


def test_app_secret_wins_over_legacy_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_SECRET", "preferred")
    monkeypatch.setenv("API_APP_KEY", "legacy")
    settings = AppSettings(_env_file=None)
    assert settings.app_secret is not None
    assert settings.app_secret.get_secret_value() == "preferred"


def test_unknown_env_keys_are_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_PASSWORD", "irrelevant")
    monkeypatch.setenv("REDIS_URL", "redis://localhost")
    settings = AppSettings(_env_file=None)
    assert settings.api_base_url == DEFAULT_API_BASE_URL


def test_env_file_is_read(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "APP_ENV=development\nAPP_SECRET=file-secret\nAPI_BASE_URL=https://host.example/api/v1\n",
        encoding="utf-8",
    )
    settings = AppSettings(_env_file=env_file)
    assert settings.app_env == "development"
    assert settings.api_base_url == "https://host.example"
    assert settings.app_secret is not None
    assert settings.app_secret.get_secret_value() == "file-secret"


def test_real_env_wins_over_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("APP_SECRET=file-secret\n", encoding="utf-8")
    monkeypatch.setenv("APP_SECRET", "real-secret")
    settings = AppSettings(_env_file=env_file)
    assert settings.app_secret is not None
    assert settings.app_secret.get_secret_value() == "real-secret"


def test_resolver_prefers_env_over_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = SecretStore(tmp_path)
    store.save("stored-secret")
    monkeypatch.setenv("APP_SECRET", "env-secret")
    resolver = SecretResolver(store, AppSettings(_env_file=None))
    assert resolver.resolve() == "env-secret"


def test_resolver_falls_back_to_store(tmp_path: Path) -> None:
    store = SecretStore(tmp_path)
    store.save("stored-secret")
    resolver = SecretResolver(store, AppSettings(_env_file=None))
    assert resolver.resolve() == "stored-secret"


def test_resolver_returns_none_when_nothing_available(tmp_path: Path) -> None:
    resolver = SecretResolver(SecretStore(tmp_path), AppSettings(_env_file=None))
    assert resolver.resolve() is None
