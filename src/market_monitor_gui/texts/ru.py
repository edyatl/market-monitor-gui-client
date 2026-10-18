"""Operator-facing Russian strings.

This is the ONLY module that contains user-visible text. Everything else imports
constants from here (directly or by key via :func:`text_for`) and never hardcodes
Russian literals.

Naming convention: ``UPPER_SNAKE_CASE``, grouped by area. A constant whose value is
an empty string is a placeholder filled in when its screen is implemented; list such
constants in :data:`EMPTY_PLACEHOLDERS`.

Ruff's ambiguous-Unicode rules are disabled for this file only (see ``pyproject.toml``).
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

# --- Application -------------------------------------------------------------

APP_NAME: Final[str] = "Market Monitor"

# --- Sidebar / navigation ----------------------------------------------------

SIDEBAR_OVERVIEW: Final[str] = "Обзор"
SIDEBAR_GROUPS: Final[str] = "Группы"
SIDEBAR_SETTINGS: Final[str] = "Настройки"
SIDEBAR_FILTERS: Final[str] = "Исключения"
SIDEBAR_HELP: Final[str] = "Помощь"

# --- Application menu --------------------------------------------------------

MENU_CONNECTION_SETTINGS: Final[str] = "Настройки подключения"
MENU_CHECK_CONNECTION: Final[str] = "Проверить соединение"
MENU_LOGOUT: Final[str] = "Выйти"
MENU_ABOUT: Final[str] = "О программе"

# --- Common actions ----------------------------------------------------------

ACTION_LOGIN: Final[str] = "Войти"
ACTION_LOGIN_AGAIN: Final[str] = "Войти снова"
ACTION_RETRY: Final[str] = "Повторить"
ACTION_CANCEL: Final[str] = "Отмена"
ACTION_SAVE: Final[str] = "Сохранить"
ACTION_ADD: Final[str] = "Добавить"
ACTION_EDIT: Final[str] = "Изменить"
ACTION_DELETE: Final[str] = "Удалить"
ACTION_REFRESH: Final[str] = "Обновить"
ACTION_CLOSE: Final[str] = "Закрыть"
ACTION_ENABLE: Final[str] = "Включить"
ACTION_DISABLE: Final[str] = "Выключить"
ACTION_DISABLE_GROUP: Final[str] = "Отключить группу"

# --- Connection state (always text + glyph, never colour alone) --------------

STATUS_CONNECTING: Final[str] = "○ Подключение…"
STATUS_CONNECTED: Final[str] = "● Подключено"
STATUS_RETRYING: Final[str] = "◌ Повторная попытка…"
STATUS_OFFLINE: Final[str] = "○ Нет связи"
STATUS_SESSION_EXPIRED: Final[str] = "◍ Сессия истекла"

# --- Login dialog ------------------------------------------------------------

LOGIN_TITLE: Final[str] = "Вход"
LOGIN_SECRET_LABEL: Final[str] = "Секрет приложения"
LOGIN_HELP: Final[str] = (
    "Введите общий секрет приложения. Он используется только для входа "
    "и не сохраняется в открытом виде."
)
LOGIN_IN_PROGRESS: Final[str] = "Выполняется вход…"
LOGIN_SUCCESS: Final[str] = "Вход выполнен"
LOGIN_FAILED: Final[str] = "Не удалось войти. Проверьте секрет и повторите."

# --- Domain labels (shared by screens) ---------------------------------------

LABEL_THRESHOLD: Final[str] = "Порог снижения цены, %"
LABEL_FILTER_PHRASES: Final[str] = "Фразы-исключения"

# --- Errors ------------------------------------------------------------------
# Tone: say what happened and what to do next. Never expose HTTP bodies, raw
# exception text, or API English messages to the operator.

ERR_NETWORK: Final[str] = "Не удалось связаться с сервером. Проверьте соединение и повторите."
ERR_TIMEOUT: Final[str] = "Сервер не ответил вовремя. Повторите попытку."
ERR_UNAUTHORIZED: Final[str] = "Требуется вход. Введите секрет приложения."
ERR_SESSION_EXPIRED: Final[str] = "Сессия истекла. Войдите снова."
ERR_FORBIDDEN: Final[str] = "Доступ запрещён."
ERR_NOT_FOUND: Final[str] = "Запись не найдена. Обновите данные."
ERR_VALIDATION: Final[str] = "Проверьте введённые данные."
ERR_CONFLICT: Final[str] = "Не удалось выполнить действие: запись используется."
ERR_CONFLICT_GROUP_IN_USE: Final[str] = (
    "Группу нельзя удалить: она используется. Отключите её вместо удаления."
)
ERR_RATE_LIMIT: Final[str] = "Слишком много запросов. Подождите и повторите."
ERR_SERVER: Final[str] = "Ошибка на сервере. Повторите позже."
ERR_BAD_RESPONSE: Final[str] = "Сервер вернул неожиданный ответ."
ERR_NO_SECRET: Final[str] = "Секрет приложения не задан. Войдите заново."
ERR_SECRET_REQUIRED: Final[str] = "Введите секрет приложения."

# --- Screen placeholders (empty until the screens batch) ---------------------

EMPTY_OVERVIEW: Final[str] = ""
EMPTY_GROUPS: Final[str] = ""
EMPTY_SETTINGS: Final[str] = ""
EMPTY_FILTERS: Final[str] = ""
EMPTY_HELP: Final[str] = ""

# --- Registry ----------------------------------------------------------------


def _collect_keys() -> dict[str, str]:
    """Collect every public ``UPPER_CASE`` string constant in this module."""
    return {
        name: value
        for name, value in globals().items()
        if name.isupper() and not name.startswith("_") and isinstance(value, str)
    }


TEXT_KEYS: Final[Mapping[str, str]] = MappingProxyType(_collect_keys())

EMPTY_PLACEHOLDERS: Final[frozenset[str]] = frozenset(
    {
        "EMPTY_OVERVIEW",
        "EMPTY_GROUPS",
        "EMPTY_SETTINGS",
        "EMPTY_FILTERS",
        "EMPTY_HELP",
    }
)


def text_for(key: str) -> str:
    """Return the Russian text registered under ``key``.

    Raises:
        KeyError: if the key is unknown. The message names the key only and never
            includes a secret; callers must not swallow this as operator text.
    """
    try:
        return TEXT_KEYS[key]
    except KeyError:
        raise KeyError(f"unknown text key: {key}") from None
