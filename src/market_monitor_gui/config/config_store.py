"""Persisted, non-secret configuration (``config.json``).

Holds the API origin. This is the **single source of truth** for the API base URL;
the SQLite ``ui_state`` table intentionally does not store it. The shared secret is
*never* written here — it lives in the encrypted secret store.
"""

from __future__ import annotations

import os
from contextlib import suppress
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from market_monitor_gui.config.urls import DEFAULT_API_BASE_URL, normalize_api_origin
from market_monitor_gui.platforms import ensure_data_dir

CONFIG_FILENAME = "config.json"
CONFIG_VERSION = 1

_FILE_MODE = 0o600


class AppConfig(BaseModel):
    """On-disk configuration model."""

    model_config = ConfigDict(extra="ignore")

    version: int = CONFIG_VERSION
    api_base_url: str = DEFAULT_API_BASE_URL

    @field_validator("api_base_url")
    @classmethod
    def _normalize_origin(cls, value: str) -> str:
        return normalize_api_origin(value)


class ConfigStore:
    """Read and write :class:`AppConfig` atomically with private permissions."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    @classmethod
    def in_data_dir(cls) -> ConfigStore:
        return cls(ensure_data_dir() / CONFIG_FILENAME)

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> AppConfig:
        """Load the config, falling back to defaults when missing or unreadable."""
        try:
            raw = self._path.read_text(encoding="utf-8")
        except OSError:
            return AppConfig()
        try:
            return AppConfig.model_validate_json(raw)
        except ValidationError:
            return AppConfig()

    def save(self, config: AppConfig) -> None:
        """Write ``config`` atomically, replacing any previous file."""
        self._atomic_write(config.model_dump_json(indent=2))

    def save_api_base_url(self, url: str) -> AppConfig:
        """Normalize ``url``, persist it, and return the saved config."""
        config = self.load()
        config.api_base_url = normalize_api_origin(url)
        self.save(config)
        return config

    def api_base_url(self) -> str:
        """Return the configured origin (default when unset)."""
        return self.load().api_base_url

    def _atomic_write(self, text: str) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_name(self._path.name + ".tmp")
        try:
            with suppress(OSError):
                tmp_path.unlink()
            fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, _FILE_MODE)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(text)
            os.replace(tmp_path, self._path)
        finally:
            with suppress(OSError):
                tmp_path.unlink()
