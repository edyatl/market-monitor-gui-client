"""Thread-safe SQLite connection wrapper.

SQLite objects are not shareable across threads by default. The GUI runs storage
work on worker threads, so this wrapper uses a single connection created with
``check_same_thread=False`` and serializes every access with an ``RLock``. Storage
traffic for UI state and caching is tiny, so a single guarded connection is both
simpler and safe.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import cast

from market_monitor_gui.db.schema import apply_schema

_BUSY_TIMEOUT_MS = 5000

Params = Sequence[object] | dict[str, object]


class Database:
    """A single-connection, lock-guarded SQLite database."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        if str(self._path) != ":memory:":
            self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._configure()
        apply_schema(self._conn)

    def _configure(self) -> None:
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
        self._conn.execute("PRAGMA foreign_keys = ON")

    @property
    def path(self) -> Path:
        return self._path

    @property
    def connection(self) -> sqlite3.Connection:
        """The underlying connection. Callers must hold :meth:`transaction`."""
        return self._conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Yield the connection inside the lock, committing on success."""
        with self._lock:
            try:
                yield self._conn
            except BaseException:
                self._conn.rollback()
                raise
            else:
                self._conn.commit()

    def execute(self, sql: str, params: Params = ()) -> sqlite3.Cursor:
        """Execute one statement and commit."""
        with self._lock:
            cursor = self._conn.execute(sql, params)
            self._conn.commit()
            return cursor

    def query_one(self, sql: str, params: Params = ()) -> sqlite3.Row | None:
        with self._lock:
            row = self._conn.execute(sql, params).fetchone()
            return cast("sqlite3.Row | None", row)

    def query_all(self, sql: str, params: Params = ()) -> list[sqlite3.Row]:
        with self._lock:
            return list(self._conn.execute(sql, params).fetchall())

    def executemany(self, sql: str, seq: Iterable[Params]) -> None:
        with self._lock:
            self._conn.executemany(sql, list(seq))
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()
