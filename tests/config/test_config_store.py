"""G3: persisted non-secret configuration."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from market_monitor_gui.config.config_store import CONFIG_FILENAME, ConfigStore
from market_monitor_gui.config.urls import DEFAULT_API_BASE_URL, normalize_api_origin
from market_monitor_gui.platforms import _constants

pytestmark = pytest.mark.unit


def test_missing_file_returns_defaults(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")
    config = store.load()
    assert config.api_base_url == DEFAULT_API_BASE_URL
    assert store.api_base_url() == DEFAULT_API_BASE_URL


def test_save_and_reload_round_trip(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")
    store.save_api_base_url("http://localhost:8000/api/v1")
    assert store.api_base_url() == "http://localhost:8000"
    assert store.load().api_base_url == "http://localhost:8000"


def test_save_normalizes_input(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")
    saved = store.save_api_base_url("  HTTPS://Host.Example/api/v1/  ")
    assert saved.api_base_url == "https://host.example"
    assert "HTTPS" not in (tmp_path / "config.json").read_text(encoding="utf-8")


def test_invalid_url_in_file_falls_back_to_defaults(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text('{"version": 1, "api_base_url": "ftp://bad"}', encoding="utf-8")
    assert ConfigStore(path).api_base_url() == DEFAULT_API_BASE_URL


def test_corrupt_file_falls_back_to_defaults(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{not json", encoding="utf-8")
    assert ConfigStore(path).api_base_url() == DEFAULT_API_BASE_URL


def test_atomic_write_leaves_no_temp_file(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")
    store.save_api_base_url("https://host.example")
    leftovers = [p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp")]
    assert leftovers == []
    assert (tmp_path / "config.json").is_file()


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")
def test_config_file_is_private(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")
    store.save_api_base_url("https://host.example")
    assert (tmp_path / "config.json").stat().st_mode & 0o777 == 0o600


def test_config_file_contains_no_secret_like_field(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")
    store.save_api_base_url("https://host.example")
    text = (tmp_path / "config.json").read_text(encoding="utf-8")
    assert "secret" not in text.lower()


def test_in_data_dir_uses_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(_constants.DATA_DIR_ENV, str(tmp_path / "data"))
    store = ConfigStore.in_data_dir()
    assert store.path == tmp_path / "data" / CONFIG_FILENAME


def test_normalize_helper_matches_store_behaviour(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")
    raw = "https://Host.Example/api/v1"
    assert store.save_api_base_url(raw).api_base_url == normalize_api_origin(raw)
