"""Tk-free form validation and outcome helpers.

Keeping this logic out of the widgets lets the login/connection paths be unit-tested
without a display, and keeps operator text in :mod:`market_monitor_gui.texts.ru`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

from market_monitor_gui.config.urls import (
    is_default_origin,
    is_loopback_origin,
    normalize_api_origin,
)
from market_monitor_gui.services.errors import login_failure_text_key


@dataclass(frozen=True, slots=True)
class OriginInput:
    """Result of validating an API origin field.

    Exactly one of ``origin`` (valid) or ``error`` (invalid) is set. ``warning`` may
    accompany a valid origin and is non-blocking.
    """

    origin: str | None
    error: str | None
    warning: str | None


@dataclass(frozen=True, slots=True)
class LoginFormValues:
    """Login dialog values; ``secret`` is ``None`` when the stored secret is used."""

    secret: str | None
    remember: bool


@dataclass(frozen=True, slots=True)
class ConnectionFormValues:
    """Connection dialog values ready for the save use-case.

    ``secret`` is set only when the operator typed a new one; ``remember`` mirrors the
    "keep the secret on this computer" checkbox (off = delete the stored secret).
    """

    origin: str
    secret: str | None
    remember: bool


#: Group name max length, mirroring the API contract (server remains authoritative).
GROUP_NAME_MAX_LEN: Final[int] = 200

#: Filter phrase max length, mirroring the API contract (server remains authoritative).
FILTER_PHRASE_MAX_LEN: Final[int] = 500

#: Price-drop threshold bounds (percent), mirroring the API contract.
THRESHOLD_MIN: Final[float] = 0.1
THRESHOLD_MAX: Final[float] = 100.0


@dataclass(frozen=True, slots=True)
class GroupFormValues:
    """Trimmed, validated group form values ready for the API."""

    name: str
    url: str
    enabled: bool


@dataclass(frozen=True, slots=True)
class GroupFormResult:
    """Result of validating the group editor form.

    Exactly one of ``values`` (valid) or ``error`` (a ``ru`` text key) is set.
    """

    values: GroupFormValues | None
    error: str | None


def validate_group_form(name: str, url: str, enabled: bool) -> GroupFormResult:
    """Lightly validate the group editor fields; the server stays authoritative."""
    clean_name = name.strip()
    clean_url = url.strip()
    if not clean_name:
        return GroupFormResult(None, "GROUP_NAME_REQUIRED")
    if len(clean_name) > GROUP_NAME_MAX_LEN:
        return GroupFormResult(None, "GROUP_NAME_TOO_LONG")
    if not clean_url:
        return GroupFormResult(None, "GROUP_URL_REQUIRED")
    if not looks_like_http_url(clean_url):
        return GroupFormResult(None, "GROUP_URL_INVALID")
    return GroupFormResult(GroupFormValues(clean_name, clean_url, enabled), None)


def looks_like_http_url(value: str) -> bool:
    """Return whether ``value`` starts with an ``http://`` or ``https://`` scheme.

    Used both to validate the group editor and to gate external link launches.
    """
    lowered = value.lower()
    return lowered.startswith(("http://", "https://"))


@dataclass(frozen=True, slots=True)
class ThresholdInput:
    """Result of validating the price-drop threshold field.

    Exactly one of ``value`` (valid percent) or ``error`` (a ``ru`` text key) is set.
    """

    value: float | None
    error: str | None


def parse_threshold_percent(raw: str) -> ThresholdInput:
    """Parse a percent value accepting either a comma or a dot decimal separator.

    The server is authoritative; this is a fast local guard so the operator gets a
    Russian message without a round-trip.
    """
    cleaned = raw.strip().replace(",", ".")
    if not cleaned:
        return ThresholdInput(None, "SETTINGS_THRESHOLD_REQUIRED")
    try:
        value = float(cleaned)
    except ValueError:
        return ThresholdInput(None, "SETTINGS_THRESHOLD_NOT_A_NUMBER")
    if not math.isfinite(value):
        return ThresholdInput(None, "SETTINGS_THRESHOLD_NOT_A_NUMBER")
    if not THRESHOLD_MIN <= value <= THRESHOLD_MAX:
        return ThresholdInput(None, "SETTINGS_THRESHOLD_OUT_OF_RANGE")
    return ThresholdInput(value, None)


@dataclass(frozen=True, slots=True)
class FilterFormValues:
    """Trimmed, validated exclusion-phrase form values ready for the API."""

    phrase: str


@dataclass(frozen=True, slots=True)
class FilterFormResult:
    """Result of validating the filter editor form.

    Exactly one of ``values`` (valid) or ``error`` (a ``ru`` text key) is set.
    """

    values: FilterFormValues | None
    error: str | None


def validate_filter_form(phrase: str) -> FilterFormResult:
    """Lightly validate the exclusion phrase; the server stays authoritative."""
    clean_phrase = phrase.strip()
    if not clean_phrase:
        return FilterFormResult(None, "FILTER_PHRASE_REQUIRED")
    if len(clean_phrase) > FILTER_PHRASE_MAX_LEN:
        return FilterFormResult(None, "FILTER_PHRASE_TOO_LONG")
    return FilterFormResult(FilterFormValues(clean_phrase), None)


def validate_origin_input(raw: str) -> OriginInput:
    """Normalize and classify a user-entered API origin.

    ``http://`` is accepted for loopback hosts without warning; for any other host it
    is accepted with the ``CONN_WRN_NOT_HTTPS`` warning text (never a hard block).
    """
    try:
        origin = normalize_api_origin(raw)
    except ValueError:
        return OriginInput(None, "CONN_ORIGIN_INVALID", None)
    return OriginInput(origin, None, _origin_warning(origin))


def _origin_warning(origin: str) -> str | None:
    if origin.startswith("http://") and not is_loopback_origin(origin):
        return "CONN_WRN_NOT_HTTPS"
    return None


def custom_origin_warning(origin: str) -> str | None:
    """Return a warning when ``origin`` is not the built-in production address."""
    return None if is_default_origin(origin) else "CONN_CUSTOM_ORIGIN_WARNING"


def validate_secret_input(raw: str) -> str | None:
    """Return an error text key for ``raw``, or ``None`` when it is usable."""
    return None if raw.strip() else "ERR_SECRET_REQUIRED"


def login_error_text(exc: BaseException) -> str:
    """Return the login-dialog message key for a failed sign-in."""
    return login_failure_text_key(exc)
