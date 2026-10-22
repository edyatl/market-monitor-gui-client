"""G19: connection/secret use-case (store, forget, origin save) without Tk."""

from __future__ import annotations

from pathlib import Path

import pytest

from market_monitor_gui.config.config_store import ConfigStore
from market_monitor_gui.config.secret_store import SecretStore
from market_monitor_gui.services.connection import forget_secret, save_connection, store_secret

pytestmark = pytest.mark.unit

ORIGIN = "https://api.test.example"


def _stores(tmp_path: Path) -> tuple[ConfigStore, SecretStore]:
    return ConfigStore(tmp_path / "config.json"), SecretStore(tmp_path)


def test_save_connection_stores_a_new_secret(tmp_path: Path) -> None:
    config, secrets = _stores(tmp_path)
    outcome = save_connection(config, secrets, origin=ORIGIN, secret="dummy", save_secret=True)
    assert outcome.ok
    assert secrets.load() == "dummy"
    assert config.load().api_base_url == ORIGIN


def test_save_connection_keeps_the_secret_with_an_empty_field(tmp_path: Path) -> None:
    config, secrets = _stores(tmp_path)
    secrets.save("existing")
    outcome = save_connection(config, secrets, origin=ORIGIN, secret=None, save_secret=True)
    assert outcome.ok
    assert secrets.load() == "existing"


def test_save_connection_clears_the_secret_when_the_box_is_off(tmp_path: Path) -> None:
    config, secrets = _stores(tmp_path)
    secrets.save("existing")
    outcome = save_connection(
        config, secrets, origin=ORIGIN, secret="typed", save_secret=False, clear_secret=True
    )
    assert outcome.ok
    assert secrets.load() is None


def test_store_and_forget_secret_round_trip(tmp_path: Path) -> None:
    _, secrets = _stores(tmp_path)
    assert store_secret(secrets, "dummy").ok
    assert secrets.load() == "dummy"
    assert forget_secret(secrets).ok
    assert secrets.load() is None


def test_save_connection_reports_an_unwritable_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, secrets = _stores(tmp_path)

    def boom(_secret: str) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(secrets, "save", boom)
    outcome = save_connection(config, secrets, origin=ORIGIN, secret="dummy", save_secret=True)
    assert not outcome.ok
    assert outcome.error_key == "ERR_UNEXPECTED"
