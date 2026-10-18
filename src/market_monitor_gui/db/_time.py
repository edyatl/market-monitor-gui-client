"""UTC timestamp helpers shared by the storage layer."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return utc_now().isoformat()


def parse_iso(value: str) -> datetime:
    """Parse an ISO-8601 string into a timezone-aware UTC datetime.

    Naive strings (written by older code) are interpreted as UTC.
    """
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
