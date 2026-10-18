"""G2: the SQLite connection wrapper and schema."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import pytest

from market_monitor_gui.db.database import Database
from market_monitor_gui.db.schema import SCHEMA_VERSION, schema_version

pytestmark = pytest.mark.unit


def test_creates_database_file_and_parent_dirs(tmp_path: Path) -> None:
    db_file = tmp_path / "nested" / "state.db"
    db = Database(db_file)
    assert db_file.exists()
    db.close()


def test_schema_is_applied_with_version(tmp_path: Path) -> None:
    db = Database(tmp_path / "state.db")
    assert schema_version(db.connection) == SCHEMA_VERSION
    tables = {
        str(row["name"])
        for row in db.query_all("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    assert {"ui_state", "cache_entries"} <= tables
    db.close()


def test_apply_schema_twice_is_idempotent(tmp_path: Path) -> None:
    db_file = tmp_path / "state.db"
    first = Database(db_file)
    first.close()
    second = Database(db_file)  # re-applies schema on an existing database
    assert schema_version(second.connection) == SCHEMA_VERSION
    second.close()


def test_transaction_rolls_back_on_error(tmp_path: Path) -> None:
    db = Database(tmp_path / "state.db")
    with pytest.raises(RuntimeError), db.transaction() as conn:
        conn.execute("INSERT INTO ui_state VALUES ('k', 'v', 'now')")
        raise RuntimeError("boom")
    assert db.query_one("SELECT value FROM ui_state WHERE key = 'k'") is None
    db.close()


def test_execute_commits(tmp_path: Path) -> None:
    db = Database(tmp_path / "state.db")
    db.execute("INSERT INTO ui_state VALUES (?, ?, ?)", ("k", "v", "now"))
    assert db.query_one("SELECT value FROM ui_state WHERE key = 'k'") is not None
    db.close()


def test_concurrent_access_from_threads(tmp_path: Path) -> None:
    db = Database(tmp_path / "state.db")
    errors: list[BaseException] = []

    def worker(offset: int) -> None:
        try:
            for i in range(50):
                db.execute(
                    "INSERT OR REPLACE INTO ui_state VALUES (?, ?, ?)",
                    (f"k{offset}-{i}", "v", "now"),
                )
        except BaseException as exc:  # surface any thread failure in the assertion
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors
    assert db.query_one("SELECT COUNT(*) AS c FROM ui_state") is not None
    count_row = db.query_one("SELECT COUNT(*) AS c FROM ui_state")
    assert count_row is not None and int(count_row["c"]) == 200
    db.close()


def test_memory_database_supported() -> None:
    db = Database(":memory:")
    assert schema_version(db.connection) == SCHEMA_VERSION
    db.close()


def test_row_factory_returns_rows(tmp_path: Path) -> None:
    db = Database(tmp_path / "state.db")
    row = db.query_one("SELECT 1 AS one")
    assert isinstance(row, sqlite3.Row)
    assert row["one"] == 1
    assert db.query_one("SELECT 1 AS one WHERE 0") is None
    db.close()
