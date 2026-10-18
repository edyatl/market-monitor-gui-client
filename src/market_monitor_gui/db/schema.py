"""SQLite schema definition and versioning for local GUI storage."""

from __future__ import annotations

import sqlite3

#: Bump when the DDL below changes; stored in ``PRAGMA user_version``.
SCHEMA_VERSION = 1

_DDL: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS ui_state (
        key        TEXT PRIMARY KEY,
        value      TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cache_entries (
        server     TEXT NOT NULL,
        key        TEXT NOT NULL,
        payload    TEXT NOT NULL,
        fetched_at TEXT NOT NULL,
        PRIMARY KEY (server, key)
    )
    """,
)


def apply_schema(conn: sqlite3.Connection) -> None:
    """Create tables if missing and record the schema version. Idempotent."""
    for statement in _DDL:
        conn.execute(statement)
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    conn.commit()


def schema_version(conn: sqlite3.Connection) -> int:
    """Return the ``user_version`` recorded in the database."""
    row = conn.execute("PRAGMA user_version").fetchone()
    if row is None:
        return 0
    return int(row[0])
