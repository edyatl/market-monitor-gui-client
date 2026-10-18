"""G2: cached API payload store."""

from __future__ import annotations

from datetime import UTC, timedelta
from pathlib import Path

import pytest

from market_monitor_gui.db._time import utc_now
from market_monitor_gui.db.cache import TABLE, CacheKey, CacheStore, JsonValue
from market_monitor_gui.db.database import Database

pytestmark = pytest.mark.unit

SERVER_A = "https://a.example"
SERVER_B = "https://b.example"


@pytest.fixture
def store(tmp_path: Path) -> CacheStore:
    return CacheStore(Database(tmp_path / "state.db"))


def test_load_missing_returns_none(store: CacheStore) -> None:
    assert store.load(SERVER_A, CacheKey.GROUPS) is None


def test_round_trip_list_payload(store: CacheStore) -> None:
    payload: JsonValue = [{"id": 1, "name": "g1"}, {"id": 2, "name": "g2"}]
    store.set_json(SERVER_A, CacheKey.GROUPS, payload)
    entry = store.load(SERVER_A, CacheKey.GROUPS)
    assert entry is not None
    assert entry.payload == payload
    assert entry.key == CacheKey.GROUPS
    assert entry.server == SERVER_A


def test_round_trip_scalar_and_none_payload(store: CacheStore) -> None:
    store.set_json(SERVER_A, CacheKey.SETTINGS, {"price_drop_threshold_percent": 5.5})
    entry = store.load(SERVER_A, CacheKey.SETTINGS)
    assert entry is not None
    assert entry.payload == {"price_drop_threshold_percent": 5.5}

    store.set_json(SERVER_A, "empty", None)
    empty_entry = store.load(SERVER_A, "empty")
    assert empty_entry is not None and empty_entry.payload is None


def test_entries_are_isolated_per_server(store: CacheStore) -> None:
    store.set_json(SERVER_A, CacheKey.GROUPS, [{"id": 1}])
    store.set_json(SERVER_B, CacheKey.GROUPS, [{"id": 2}])
    entry_a = store.load(SERVER_A, CacheKey.GROUPS)
    entry_b = store.load(SERVER_B, CacheKey.GROUPS)
    assert entry_a is not None and entry_b is not None
    assert entry_a.payload == [{"id": 1}]
    assert entry_b.payload == [{"id": 2}]


def test_set_replaces_previous_payload(store: CacheStore) -> None:
    store.set_json(SERVER_A, CacheKey.GROUPS, [{"id": 1}])
    store.set_json(SERVER_A, CacheKey.GROUPS, [{"id": 9}])
    entry = store.load(SERVER_A, CacheKey.GROUPS)
    assert entry is not None and entry.payload == [{"id": 9}]


def test_delete(store: CacheStore) -> None:
    store.set_json(SERVER_A, CacheKey.GROUPS, [])
    store.delete(SERVER_A, CacheKey.GROUPS)
    assert store.load(SERVER_A, CacheKey.GROUPS) is None


def test_clear_one_server_only(store: CacheStore) -> None:
    store.set_json(SERVER_A, CacheKey.GROUPS, [])
    store.set_json(SERVER_B, CacheKey.GROUPS, [])
    store.clear(SERVER_A)
    assert store.load(SERVER_A, CacheKey.GROUPS) is None
    assert store.load(SERVER_B, CacheKey.GROUPS) is not None


def test_clear_all(store: CacheStore) -> None:
    store.set_json(SERVER_A, CacheKey.GROUPS, [])
    store.set_json(SERVER_B, CacheKey.FILTERS, [])
    store.clear_all()
    assert store.load(SERVER_A, CacheKey.GROUPS) is None
    assert store.load(SERVER_B, CacheKey.FILTERS) is None


def test_corrupt_payload_returns_none(tmp_path: Path) -> None:
    db = Database(tmp_path / "state.db")
    db.execute(
        f"INSERT INTO {TABLE} VALUES (?, ?, ?, ?)",
        (SERVER_A, CacheKey.GROUPS, "{not json", utc_now().isoformat()),
    )
    corrupt_store = CacheStore(db)
    assert corrupt_store.load(SERVER_A, CacheKey.GROUPS) is None


def test_corrupt_timestamp_returns_none(tmp_path: Path) -> None:
    db = Database(tmp_path / "state.db")
    db.execute(
        f"INSERT INTO {TABLE} VALUES (?, ?, ?, ?)",
        (SERVER_A, CacheKey.GROUPS, "[]", "not-a-date"),
    )
    corrupt_store = CacheStore(db)
    assert corrupt_store.load(SERVER_A, CacheKey.GROUPS) is None


def test_age_seconds_is_recent_and_never_negative(store: CacheStore) -> None:
    store.set_json(SERVER_A, CacheKey.GROUPS, [])
    entry = store.load(SERVER_A, CacheKey.GROUPS)
    assert entry is not None
    assert 0.0 <= entry.age_seconds < 60.0


def test_age_seconds_reflects_fetch_time(tmp_path: Path) -> None:
    db = Database(tmp_path / "state.db")
    old = utc_now() - timedelta(hours=2)
    db.execute(
        f"INSERT INTO {TABLE} VALUES (?, ?, ?, ?)",
        (SERVER_A, CacheKey.GROUPS, "[]", old.astimezone(UTC).isoformat()),
    )
    entry = CacheStore(db).load(SERVER_A, CacheKey.GROUPS)
    assert entry is not None
    assert entry.age_seconds >= 7000.0


def test_large_payload_round_trips(store: CacheStore) -> None:
    payload: JsonValue = [{"id": i, "name": f"group-{i}"} for i in range(2000)]
    store.set_json(SERVER_A, CacheKey.GROUPS, payload)
    entry = store.load(SERVER_A, CacheKey.GROUPS)
    assert entry is not None and entry.payload == payload


def test_cache_key_enum_values_are_stable() -> None:
    assert CacheKey.GROUPS.value == "groups"
    assert CacheKey.DASHBOARD_SUMMARY.value == "dashboard_summary"
    assert str(CacheKey.FILTERS) == "filters"
