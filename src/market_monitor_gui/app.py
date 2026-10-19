"""Composition root: build the non-UI collaborators the shell needs.

Kept free of Tkinter so it is importable and testable without a display. The
CustomTkinter shell (:mod:`market_monitor_gui.ui.app`) consumes an :class:`AppContext`
and owns widget creation and the main loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from market_monitor_gui.api.client import ApiClient
from market_monitor_gui.background.task_runner import TaskRunner
from market_monitor_gui.config.config_store import ConfigStore
from market_monitor_gui.config.resolver import SecretResolver
from market_monitor_gui.config.secret_store import SecretStore
from market_monitor_gui.config.settings import AppSettings
from market_monitor_gui.config.urls import DEFAULT_API_BASE_URL
from market_monitor_gui.db.cache import CacheStore
from market_monitor_gui.db.database import Database
from market_monitor_gui.db.ui_state import UiStateStore
from market_monitor_gui.platforms import ensure_data_dir

STATE_DB_FILENAME: Final[str] = "state.db"


def resolve_startup_origin(config: ConfigStore, settings: AppSettings) -> str:
    """Pick the API origin to start with.

    The persisted config is the source of truth; ``API_BASE_URL`` acts as a dev
    override only when it differs from the built-in default.
    """
    if settings.api_base_url != DEFAULT_API_BASE_URL:
        return settings.api_base_url
    return config.api_base_url()


@dataclass(slots=True)
class AppContext:
    """Non-UI collaborators, wired once at startup and shared by the shell."""

    settings: AppSettings
    config: ConfigStore
    secrets: SecretStore
    resolver: SecretResolver
    database: Database
    ui_state: UiStateStore
    cache: CacheStore
    api: ApiClient
    runner: TaskRunner

    @classmethod
    def create(cls, settings: AppSettings | None = None) -> AppContext:
        resolved = settings if settings is not None else AppSettings()
        data_dir = ensure_data_dir()
        config = ConfigStore.in_data_dir()
        secrets = SecretStore.in_data_dir()
        resolver = SecretResolver(secrets, resolved)
        database = Database(data_dir / STATE_DB_FILENAME)
        ui_state = UiStateStore(database)
        cache = CacheStore(database)
        api = ApiClient.create(resolve_startup_origin(config, resolved))
        return cls(
            settings=resolved,
            config=config,
            secrets=secrets,
            resolver=resolver,
            database=database,
            ui_state=ui_state,
            cache=cache,
            api=api,
            runner=TaskRunner(),
        )

    def close(self) -> None:
        """Release the runner, HTTP client, and database connection."""
        self.runner.shutdown()
        self.api.close()
        self.database.close()
