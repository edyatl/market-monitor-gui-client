"""G13: external-link launching is http/https only and never crashes the UI."""

from __future__ import annotations

import webbrowser
from collections.abc import Callable

import pytest

from market_monitor_gui.ui import links
from market_monitor_gui.ui.forms import looks_like_http_url

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "value",
    ["http://example.org", "https://example.org", "HTTPS://EXAMPLE.ORG", "  https://a/b  "],
)
def test_looks_like_http_url_accepts_http_and_https(value: str) -> None:
    assert looks_like_http_url(value.strip()) is True


@pytest.mark.parametrize(
    "value",
    [
        "",
        "example.org",
        "www.example.org",
        "ftp://example.org",
        "file:///etc/passwd",
        "javascript:1",
    ],
)
def test_looks_like_http_url_rejects_everything_else(value: str) -> None:
    assert looks_like_http_url(value) is False


def _patch_browser(
    monkeypatch: pytest.MonkeyPatch, behaviour: Callable[[str, int], bool] | Exception
) -> list[tuple[str, int]]:
    calls: list[tuple[str, int]] = []

    def fake_open(url: str, new: int = 0) -> bool:
        calls.append((url, new))
        if isinstance(behaviour, Exception):
            raise behaviour
        return behaviour(url, new)

    monkeypatch.setattr(webbrowser, "open", fake_open)
    return calls


def test_open_external_url_launches_http_in_a_new_tab(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _patch_browser(monkeypatch, lambda _url, _new: True)
    assert links.open_external_url("https://shop.example/1") is True
    assert calls == [("https://shop.example/1", 2)]


def test_open_external_url_trims_surrounding_whitespace(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _patch_browser(monkeypatch, lambda _url, _new: True)
    assert links.open_external_url("  https://shop.example/1  ") is True
    assert calls == [("https://shop.example/1", 2)]


@pytest.mark.parametrize("url", ["ftp://shop.example", "javascript:alert(1)", "", "shop.example"])
def test_open_external_url_refuses_non_http_without_launching(
    monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    calls = _patch_browser(monkeypatch, lambda _url, _new: True)
    assert links.open_external_url(url) is False
    assert calls == []


def test_open_external_url_reports_browser_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_browser(monkeypatch, lambda _url, _new: False)
    assert links.open_external_url("https://shop.example/1") is False


def test_open_external_url_swallows_browser_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_browser(monkeypatch, webbrowser.Error("no browser"))
    assert links.open_external_url("https://shop.example/1") is False


def test_open_external_url_swallows_os_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_browser(monkeypatch, OSError("boom"))
    assert links.open_external_url("https://shop.example/1") is False
