"""G8: Tk-free Overview presentation helpers."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from market_monitor_gui.services.overview import OverviewData
from market_monitor_gui.texts import ru
from market_monitor_gui.ui.overview_view import (
    overview_cards,
    scan_run_line,
    worker_value,
)

pytestmark = pytest.mark.unit

WHEN = datetime(2026, 10, 18, 10, 0, tzinfo=UTC)


def _data(**overrides: object) -> OverviewData:
    base: dict[str, object] = {
        "groups_total": 5,
        "groups_enabled": 3,
        "products_total": 100,
        "products_active": 80,
        "products_missing": 20,
        "pending_deliveries": 4,
        "failed_deliveries": 1,
        "worker_status": "ok",
        "worker_alive": True,
        "last_successful_scan_at": WHEN,
        "latest_scan_status": None,
        "from_cache": False,
        "cached_at": None,
    }
    base.update(overrides)
    return OverviewData(**base)  # type: ignore[arg-type]


def test_overview_cards_have_expected_titles_and_values() -> None:
    cards = overview_cards(_data())
    assert [card.title for card in cards] == [
        ru.OVERVIEW_CARD_GROUPS,
        ru.OVERVIEW_CARD_PRODUCTS,
        ru.OVERVIEW_CARD_DELIVERIES,
        ru.OVERVIEW_CARD_WORKER,
        ru.OVERVIEW_CARD_LAST_SCAN,
    ]
    assert cards[0].value == ru.fmt_overview_groups(3, 5)
    assert cards[1].value == ru.fmt_overview_products(100, 80, 20)
    assert cards[2].value == ru.fmt_overview_deliveries(4, 1)
    assert cards[4].value == ru.fmt_scan_time(WHEN)


def test_scan_time_placeholder_when_never_scanned() -> None:
    cards = overview_cards(_data(last_successful_scan_at=None))
    assert cards[4].value == ru.OVERVIEW_SCAN_NEVER


def test_worker_value_uses_alive_flag() -> None:
    assert worker_value("running", True) == ru.fmt_overview_worker_alive("running")
    assert worker_value("running", False) == ru.OVERVIEW_WORKER_DEAD
    assert worker_value(None, None) == ru.OVERVIEW_WORKER_UNKNOWN
    assert worker_value("ok", None) == ru.fmt_overview_worker("ok")
    assert worker_value(None, True) == ru.OVERVIEW_WORKER_ALIVE


def test_scan_run_line_optional() -> None:
    assert scan_run_line(_data(latest_scan_status=None)) is None
    assert scan_run_line(_data(latest_scan_status="success")) == ru.fmt_overview_scan_run("success")
