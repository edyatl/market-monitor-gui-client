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
from datetime import datetime
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

# Decorative glyphs shown before each navigation label. Labels stay authoritative when a
# font lacks a glyph (rare: some Windows fonts render ⚙/☰ as tofu boxes).
SIDEBAR_ICON_OVERVIEW: Final[str] = "▦"
SIDEBAR_ICON_GROUPS: Final[str] = "▣"
SIDEBAR_ICON_FILTERS: Final[str] = "⊘"
SIDEBAR_ICON_SETTINGS: Final[str] = "⚙"
SIDEBAR_ICON_HELP: Final[str] = "?"

# --- Application menu --------------------------------------------------------

MENU_CONNECTION_SETTINGS: Final[str] = "Настройки подключения"
MENU_CHECK_CONNECTION: Final[str] = "Проверить соединение"
MENU_LOGOUT: Final[str] = "Завершить сеанс"
MENU_ABOUT: Final[str] = "О программе"
MENU_BUTTON: Final[str] = "Меню"
MENU_ICON: Final[str] = "☰"

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
STATUS_RETRYING: Final[str] = "○ Повторная попытка…"
STATUS_OFFLINE: Final[str] = "○ Нет связи"
STATUS_SESSION_EXPIRED: Final[str] = "○ Сессия истекла"

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
ERR_UNEXPECTED: Final[str] = "Непредвиденная ошибка. Повторите действие."
ERR_SECRET_SAVE: Final[str] = "Не удалось сохранить секрет. Проверьте права на папку данных."
ERR_OPEN_LINK: Final[str] = "Не удалось открыть ссылку в браузере."
ERR_NO_DISPLAY: Final[str] = "Не удалось запустить графический интерфейс: нет доступного дисплея."

# --- Connection settings dialog ----------------------------------------------

CONN_TITLE: Final[str] = "Настройки подключения"
CONN_ORIGIN_LABEL: Final[str] = "Адрес API"
CONN_ORIGIN_HELP: Final[str] = (
    "Укажите адрес сервера. Используйте https://. "
    "Обычный http:// допускается только для локальной разработки "
    "(localhost, 127.0.0.1, ::1)."
)
CONN_ORIGIN_INVALID: Final[str] = "Некорректный адрес. Пример: https://api.example.org"
CONN_WRN_NOT_HTTPS: Final[str] = (
    "Внимание: соединение без шифрования (http://). Используйте https:// вне локальной разработки."
)
CONN_CUSTOM_ORIGIN_WARNING: Final[str] = (
    "Указан адрес, отличный от адреса по умолчанию. Убедитесь, что это ваш сервер, "
    "прежде чем сохранять секрет."
)
CONN_SECRET_LABEL: Final[str] = "Секрет приложения"
CONN_SAVE_SECRET: Final[str] = "Сохранить секрет на этом компьютере"
CONN_SAVED: Final[str] = "Настройки подключения сохранены."
CONN_ORIGIN_CHANGED_RELOGIN: Final[str] = "Адрес изменён. Войдите заново."

# --- About dialog ------------------------------------------------------------

ABOUT_TITLE: Final[str] = "О программе"
ABOUT_VERSION_LABEL: Final[str] = "Версия"

# --- Status bar messages -----------------------------------------------------

STATUS_LAST_REFRESH: Final[str] = "Обновлено: {when}"
STATUS_NEVER_REFRESHED: Final[str] = "Данные ещё не загружались"

# --- Feedback glyphs (decorative; the words stay authoritative) --------------
# Kept here like the sidebar icons: operator-visible, so not hardcoded in widgets.
# Verified present in DejaVu Sans; a missing glyph is cosmetic only.

BANNER_GLYPH_LOADING: Final[str] = "◌"
BANNER_GLYPH_CACHED: Final[str] = "⚠"
BANNER_GLYPH_ERROR: Final[str] = "✗"
BANNER_GLYPH_INFO: Final[str] = "•"
MSG_GLYPH_INFO: Final[str] = "•"
MSG_GLYPH_SUCCESS: Final[str] = "✓"
MSG_GLYPH_WARN: Final[str] = "⚠"
MSG_GLYPH_ERROR: Final[str] = "✗"

# --- Check connection feedback -----------------------------------------------

STATUS_CHECK_OK: Final[str] = "Соединение в порядке."
CHECK_IN_PROGRESS: Final[str] = "Проверка соединения…"

# --- Read-only mode (cached or unavailable data) -----------------------------

READONLY_NOTICE: Final[str] = "Изменения временно недоступны."

# --- Overview screen ---------------------------------------------------------

OVERVIEW_LOADING: Final[str] = "Загрузка данных…"
OVERVIEW_SUMMARY: Final[str] = "Группы: включено {enabled} из {total}"
OVERVIEW_CARD_GROUPS: Final[str] = "Группы"
OVERVIEW_CARD_PRODUCTS: Final[str] = "Товары"
OVERVIEW_CARD_DELIVERIES: Final[str] = "Доставки"
OVERVIEW_CARD_WORKER: Final[str] = "Воркер"
OVERVIEW_CARD_LAST_SCAN: Final[str] = "Последний успешный скан"
OVERVIEW_GROUPS_VALUE: Final[str] = "включено {enabled} из {total}"
OVERVIEW_PRODUCTS_VALUE: Final[str] = "всего {total}, активных {active}, отсутствует {missing}"
OVERVIEW_DELIVERIES_VALUE: Final[str] = "в очереди {pending}, с ошибкой {failed}"
OVERVIEW_WORKER_VALUE: Final[str] = "статус: {status}"
OVERVIEW_WORKER_ALIVE: Final[str] = "● работает"
OVERVIEW_WORKER_ALIVE_DETAIL: Final[str] = "● работает — {status}"
OVERVIEW_WORKER_DEAD: Final[str] = "○ не отвечает"
OVERVIEW_WORKER_UNKNOWN: Final[str] = "○ нет данных"
OVERVIEW_SCAN_NEVER: Final[str] = "нет данных"
OVERVIEW_SCAN_RUN: Final[str] = "последний запуск: {status}"
OVERVIEW_EMPTY_HINT: Final[str] = "Нажмите «Обновить», чтобы загрузить данные."
DATA_CACHED: Final[str] = "Данные из кэша, обновлено {when}"
DATA_CACHED_READONLY: Final[str] = (
    "Данные из кэша, обновлено {when}. Изменения недоступны без связи с сервером."
)

# --- Groups screen -----------------------------------------------------------

GROUPS_LOADING: Final[str] = "Загрузка групп…"
GROUPS_EMPTY: Final[str] = "Групп пока нет. Добавьте первую."
GROUPS_COUNT: Final[str] = "Групп: {count}"
GROUPS_SAVED: Final[str] = "Группа сохранена."
GROUPS_DELETED: Final[str] = "Группа удалена."
GROUP_DISABLED: Final[str] = "Группа отключена."
GROUP_EDITOR_TITLE_ADD: Final[str] = "Добавить группу"
GROUP_EDITOR_TITLE_EDIT: Final[str] = "Изменить группу"
GROUP_NAME_LABEL: Final[str] = "Название"
GROUP_URL_LABEL: Final[str] = "Ссылка"
GROUP_ENABLED_LABEL: Final[str] = "Группа включена"
GROUP_NAME_REQUIRED: Final[str] = "Введите название группы."
GROUP_NAME_TOO_LONG: Final[str] = "Название не должно превышать 200 символов."
GROUP_URL_REQUIRED: Final[str] = "Введите ссылку на группу."
GROUP_URL_INVALID: Final[str] = "Ссылка должна начинаться с http:// или https://"
GROUP_STATE_ENABLED: Final[str] = "● Включена"
GROUP_STATE_DISABLED: Final[str] = "○ Выключена"
CONFIRM_DELETE_TITLE: Final[str] = "Удаление группы"
CONFIRM_DELETE_WARNING: Final[str] = "Действие нельзя отменить."

# --- Settings screen ---------------------------------------------------------

SETTINGS_THRESHOLD_HINT: Final[str] = (
    "Порог снижения цены в процентах. Значение действует на сервере глобально — "
    "для всех операторов."
)
SETTINGS_THRESHOLD_REQUIRED: Final[str] = "Укажите порог снижения цены."
SETTINGS_THRESHOLD_NOT_A_NUMBER: Final[str] = "Введите число, например 7,5."
SETTINGS_THRESHOLD_OUT_OF_RANGE: Final[str] = "Порог должен быть от 0,1 до 100 %."
SETTINGS_LOADING: Final[str] = "Загрузка настроек…"
SETTINGS_SAVED: Final[str] = "Настройки сохранены."

# --- Filters screen (exclusions) ---------------------------------------------

FILTERS_LOADING: Final[str] = "Загрузка исключений…"
FILTERS_EMPTY: Final[str] = "Исключений пока нет. Добавьте первое."
FILTERS_COUNT: Final[str] = "Исключений: {count}"
FILTERS_SAVED: Final[str] = "Исключение добавлено."
FILTERS_DELETED: Final[str] = "Исключение удалено."
FILTER_EDITOR_TITLE_ADD: Final[str] = "Добавить исключение"
FILTER_PHRASE_LABEL: Final[str] = "Фраза"
FILTER_PHRASE_HINT: Final[str] = (
    "Товары с этой фразой исключаются из обработки. Регистр и пробелы нормализуются на сервере."
)
FILTER_PHRASE_REQUIRED: Final[str] = "Введите фразу-исключение."
FILTER_PHRASE_TOO_LONG: Final[str] = "Фраза не должна превышать 500 символов."
FILTER_NORMALIZED_VALUE: Final[str] = "Нормализованная форма: {phrase}"
FILTER_STATE_ENABLED: Final[str] = "● Включено"
FILTER_STATE_DISABLED: Final[str] = "○ Выключено"
CONFIRM_DELETE_FILTER_TITLE: Final[str] = "Удаление исключения"

# --- Help screen -------------------------------------------------------------

HELP_INTRO_HEADING: Final[str] = "Что это за программа"
HELP_INTRO_BODY: Final[str] = (
    "Market Monitor — панель оператора для сервиса мониторинга цен. Здесь настраивают "
    "группы мониторинга, порог снижения цены и фразы-исключения и смотрят состояние "
    "сервиса. Сбором данных и отправкой уведомлений занимается сервер; программа только "
    "показывает и меняет настройки."
)
HELP_LOGIN_HEADING: Final[str] = "Вход и секрет приложения"
HELP_LOGIN_BODY: Final[str] = (
    "Для входа нужен общий секрет приложения — он используется только для входа. Если "
    "выбрано «Сохранить секрет на этом компьютере», секрет хранится в зашифрованном виде, "
    "а не открытым текстом. После входа программа работает по сессии: пока сессия жива, "
    "вводить секрет повторно не нужно."
)
HELP_OVERVIEW_HEADING: Final[str] = "Обзор"
HELP_OVERVIEW_BODY: Final[str] = (
    "Обзор показывает состояние сервиса: группы, товары, доставки, состояние воркера и "
    "последний успешный скан. «Обновить» заново читает данные с сервера, «Проверить "
    "соединение» только проверяет доступность API. Запускать или останавливать сканирование "
    "здесь нельзя."
)
HELP_GROUPS_HEADING: Final[str] = "Группы"
HELP_GROUPS_BODY: Final[str] = (
    "Группы — источники мониторинга. Группу можно добавить, изменить, включить или выключить "
    "и удалить. Выключенная группа остаётся в списке, но не обрабатывается. Если группу "
    "удалить нельзя, сервер вернёт ошибку — тогда её лучше отключить."
)
HELP_THRESHOLD_HEADING: Final[str] = "Настройки: порог снижения цены"
HELP_THRESHOLD_BODY: Final[str] = (
    "Порог снижения цены задаётся в процентах, от 0,1 до 100. Падением считается цена ≤ "
    "базовая × (1 − порог). Значение действует на сервере глобально — для всех операторов, "
    "а не только для вас. В поле можно вводить и запятую, и точку: 7,5 и 7.5 — одно и то же."
)
HELP_FILTERS_HEADING: Final[str] = "Исключения"
HELP_FILTERS_BODY: Final[str] = (
    "Исключения — фразы, по которым товары отбрасываются. Введите фразу (слова через пробел) "
    "в поле «Фраза» и нажмите «Добавить». Регистр и лишние пробелы нормализуются на сервере: "
    "в списке видно нормализованную форму, и сравнивает её сервер, а не программа."
)
HELP_OFFLINE_HEADING: Final[str] = "Если нет связи или истекла сессия"
HELP_OFFLINE_BODY: Final[str] = (
    "Когда сервер недоступен, программа показывает последние сохранённые данные с пометкой "
    "«Данные из кэша, обновлено …», а кнопки изменения остаются недоступны. Если сессия "
    "истекла, введите секрет ещё раз — данные при этом не теряются."
)
HELP_SUPPORT_HEADING: Final[str] = "Где искать ответы"
HELP_SUPPORT_BODY: Final[str] = (
    "Уведомления приходят из Telegram-бота — там же видны группы, исключения и настройки. "
    "Версию программы и сведения о сборке смотрите в меню «О программе»."
)

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


def fmt_version(version: str) -> str:
    """Format the application version for the About dialog."""
    return f"{ABOUT_VERSION_LABEL}: {version}"


def fmt_last_refresh(when: datetime | None) -> str:
    """Format the last successful refresh time, or a placeholder when never refreshed."""
    if when is None:
        return STATUS_NEVER_REFRESHED
    return STATUS_LAST_REFRESH.format(when=when.astimezone().strftime("%d.%m.%Y %H:%M"))


def fmt_overview_summary(total: int, enabled: int) -> str:
    """Format the Overview summary line."""
    return OVERVIEW_SUMMARY.format(total=total, enabled=enabled)


def fmt_datetime(when: datetime | None) -> str:
    """Format a date/time as ``dd.mm.yyyy HH:MM``, or an empty string when absent."""
    if when is None:
        return ""
    return when.astimezone().strftime("%d.%m.%Y %H:%M")


def fmt_overview_groups(enabled: int, total: int) -> str:
    """Format the Overview groups value."""
    return OVERVIEW_GROUPS_VALUE.format(enabled=enabled, total=total)


def fmt_overview_products(total: int, active: int, missing: int) -> str:
    """Format the Overview products value."""
    return OVERVIEW_PRODUCTS_VALUE.format(total=total, active=active, missing=missing)


def fmt_overview_deliveries(pending: int, failed: int) -> str:
    """Format the Overview deliveries value."""
    return OVERVIEW_DELIVERIES_VALUE.format(pending=pending, failed=failed)


def fmt_overview_worker(status: str | None) -> str:
    """Format the Overview worker status value, or a placeholder when absent."""
    if not status:
        return OVERVIEW_WORKER_UNKNOWN
    return OVERVIEW_WORKER_VALUE.format(status=status)


def fmt_overview_worker_alive(status: str | None) -> str:
    """Format the alive-worker value, appending the free-form status when present."""
    if not status:
        return OVERVIEW_WORKER_ALIVE
    return OVERVIEW_WORKER_ALIVE_DETAIL.format(status=status)


def fmt_overview_scan_run(status: str) -> str:
    """Format the secondary Overview line describing the latest scan run."""
    return OVERVIEW_SCAN_RUN.format(status=status)


def fmt_scan_time(when: datetime | None) -> str:
    """Format the last successful scan time, or a placeholder when never scanned."""
    formatted = fmt_datetime(when)
    return formatted or OVERVIEW_SCAN_NEVER


def fmt_data_cached(when: datetime | None) -> str:
    """Format the cached-data note shown when offline data is displayed."""
    formatted = fmt_datetime(when)
    return DATA_CACHED.format(when=formatted or "—")


def fmt_data_cached_readonly(when: datetime | None) -> str:
    """Format the cached-data note that also states why changes are unavailable."""
    formatted = fmt_datetime(when)
    return DATA_CACHED_READONLY.format(when=formatted or "—")


def fmt_readonly_notice(reason: str) -> str:
    """Append the read-only consequence to the reason a screen cannot be edited."""
    return f"{reason} {READONLY_NOTICE}" if reason else READONLY_NOTICE


def fmt_groups_count(count: int) -> str:
    """Format the Groups count line."""
    return GROUPS_COUNT.format(count=count)


def fmt_confirm_delete_group(name: str) -> str:
    """Format the destructive confirmation question naming the group."""
    return f"Удалить группу «{name}»?"


def fmt_filters_count(count: int) -> str:
    """Format the Filters count line."""
    return FILTERS_COUNT.format(count=count)


def fmt_filter_normalized(phrase: str) -> str:
    """Format the normalized-phrase note for a filter row."""
    return FILTER_NORMALIZED_VALUE.format(phrase=phrase)


def fmt_confirm_delete_filter(phrase: str) -> str:
    """Format the destructive confirmation question naming the exclusion phrase."""
    return f"Удалить исключение «{phrase}»?"


def fmt_menu_button() -> str:
    """Format the application-menu button label with its decorative icon."""
    return f"{MENU_ICON}  {MENU_BUTTON}"
