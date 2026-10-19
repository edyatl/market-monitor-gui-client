"""Open external links in the system browser.

Only ``http``/``https`` targets are ever handed to the browser. The scheme check is the
same one used by the group form (:func:`market_monitor_gui.ui.forms.looks_like_http_url`),
so a malicious or malformed value coming from the API can never launch ``file:``,
``javascript:`` or similar. This module performs no network I/O of its own.
"""

from __future__ import annotations

import webbrowser

from market_monitor_gui.ui.forms import looks_like_http_url


def open_external_url(url: str) -> bool:
    """Open ``url`` in the default browser; return ``False`` when refused or unavailable."""
    target = url.strip()
    if not looks_like_http_url(target):
        return False
    try:
        return webbrowser.open(target, new=2)
    except webbrowser.Error, OSError:
        return False
