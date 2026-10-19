"""Tk-free formatting helper for the Settings screen.

Keeps the display formatting out of the widgets so it can be unit-tested headless.
The threshold is shown with a decimal comma (Russian convention) so it can be
re-submitted unchanged; input accepts either comma or dot (see ``ui.forms``).
"""

from __future__ import annotations


def format_threshold(value: float) -> str:
    """Format a percent value for display: exact, with a comma and no trailing ``,0``."""
    text = repr(float(value))
    if text.endswith(".0"):
        text = text[:-2]
    return text.replace(".", ",")
