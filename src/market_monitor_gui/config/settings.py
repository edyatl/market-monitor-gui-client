"""Application settings from environment / ``.env`` (development overrides).

Read-only configuration for development. The persisted API origin lives in the
config store and the persisted secret in the Fernet secret store; these settings are
overrides that take precedence over stored values where documented.

- ``API_BASE_URL`` — origin only; a trailing ``/api/v1`` is tolerated and stripped.
- ``APP_SECRET`` — preferred shared-secret variable.
- ``API_APP_KEY`` — legacy alias, used only when ``APP_SECRET`` is unset.
"""

from __future__ import annotations

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from market_monitor_gui.config.urls import DEFAULT_API_BASE_URL, normalize_api_origin


class AppSettings(BaseSettings):
    """Environment-backed settings with safe defaults and no required values."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    api_base_url: str = Field(
        default=DEFAULT_API_BASE_URL,
        validation_alias=AliasChoices("API_BASE_URL", "api_base_url"),
    )
    app_secret: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("APP_SECRET", "API_APP_KEY", "app_secret"),
    )
    app_env: str = Field(
        default="production",
        validation_alias=AliasChoices("APP_ENV", "app_env"),
    )

    @field_validator("api_base_url")
    @classmethod
    def _normalize_origin(cls, value: str) -> str:
        return normalize_api_origin(value)
