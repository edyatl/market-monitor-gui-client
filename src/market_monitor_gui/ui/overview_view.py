"""Tk-free formatting helpers for the Overview screen.

Keeping the card/value construction out of the widgets lets the presentation be
unit-tested headless. No widget, network, or storage imports here; strings come from
:mod:`market_monitor_gui.texts.ru` only.
"""

from __future__ import annotations

from dataclasses import dataclass

from market_monitor_gui.services.overview import OverviewData
from market_monitor_gui.texts import ru


@dataclass(frozen=True, slots=True)
class MetricCard:
    """A titled read-only metric shown on the Overview screen."""

    title: str
    value: str


def overview_cards(data: OverviewData) -> list[MetricCard]:
    """Build the ordered list of Overview cards from a view-model."""
    return [
        MetricCard(
            ru.OVERVIEW_CARD_GROUPS,
            ru.fmt_overview_groups(data.groups_enabled, data.groups_total),
        ),
        MetricCard(
            ru.OVERVIEW_CARD_PRODUCTS,
            ru.fmt_overview_products(
                data.products_total, data.products_active, data.products_missing
            ),
        ),
        MetricCard(
            ru.OVERVIEW_CARD_DELIVERIES,
            ru.fmt_overview_deliveries(data.pending_deliveries, data.failed_deliveries),
        ),
        MetricCard(
            ru.OVERVIEW_CARD_WORKER,
            worker_value(data.worker_status, data.worker_alive),
        ),
        MetricCard(
            ru.OVERVIEW_CARD_LAST_SCAN,
            ru.fmt_scan_time(data.last_successful_scan_at),
        ),
    ]


def worker_value(status: str | None, alive: bool | None) -> str:
    """Compose the worker value: text (never colour alone) from the API fields.

    ``is_alive`` is an explicit contract field, so the liveness glyph is not a guess;
    the free-form ``status`` string is shown verbatim alongside it. All glyphs and
    wording come from :mod:`market_monitor_gui.texts.ru` (never hardcoded here).
    """
    if alive is False:
        return ru.OVERVIEW_WORKER_DEAD
    if alive is True:
        return ru.fmt_overview_worker_alive(status)
    return ru.fmt_overview_worker(status)


def scan_run_line(data: OverviewData) -> str | None:
    """Return the optional secondary scan-run line, or ``None`` when unavailable."""
    if not data.latest_scan_status:
        return None
    return ru.fmt_overview_scan_run(data.latest_scan_status)
