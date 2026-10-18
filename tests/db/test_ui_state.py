"""G2: UI state key/value store."""

from __future__ import annotations

from pathlib import Path

import pytest

from market_monitor_gui.db.database import Database
from market_monitor_gui.db.ui_state import DEFAULT_THEME, UiStateStore

pytestmark = pytest.mark.unit


@pytest.fixture
def store(tmp_path: Path) -> UiStateStore:
    return UiStateStore(Database(tmp_path / "state.db"))


def test_get_missing_returns_default(store: UiStateStore) -> None:
    assert store.get("nope") is None
    assert store.get("nope", "fallback") == "fallback"


def test_set_and_get_round_trip(store: UiStateStore) -> None:
    store.set("key", "value")
    assert store.get("key") == "value"


def test_set_overwrites(store: UiStateStore) -> None:
    store.set("key", "first")
    store.set("key", "second")
    assert store.get("key") == "second"


def test_stores_unicode_and_empty_values(store: UiStateStore) -> None:
    store.set("empty", "")
    store.set("unicode", "\u0433\u0440\u0443\u043f\u043f\u044b")
    assert store.get("empty") == ""
    assert store.get("unicode") == "\u0433\u0440\u0443\u043f\u043f\u044b"


def test_delete(store: UiStateStore) -> None:
    store.set("key", "value")
    store.delete("key")
    assert store.get("key") is None


def test_all_items(store: UiStateStore) -> None:
    store.set("a", "1")
    store.set("b", "2")
    assert store.all_items() == {"a": "1", "b": "2"}


def test_theme_defaults_and_round_trip(store: UiStateStore) -> None:
    assert store.get_theme() == DEFAULT_THEME
    store.set_theme("dark")
    assert store.get_theme() == "dark"


def test_last_screen_and_geometry_round_trip(store: UiStateStore) -> None:
    assert store.get_last_screen() is None
    store.set_last_screen("overview")
    assert store.get_last_screen() == "overview"
    store.set_window_geometry("900x600+10+10")
    assert store.get_window_geometry() == "900x600+10+10"
