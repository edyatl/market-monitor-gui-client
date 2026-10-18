"""Encrypted secret-at-rest store (Fernet).

Layout inside the data directory:

- ``secret.key`` — Fernet key, owner-only (``0o600``).
- ``secret.enc`` — Fernet token of the shared application secret.

The plaintext secret is never written to disk, never logged, and never returned in
an error message or ``repr``. This protects against casual disclosure only; it does
not defend against malware running as the same user.

There is no DPAPI/keyring requirement: the key file plus restrictive permissions is
the supported mechanism on both Linux and Windows.
"""

from __future__ import annotations

import logging
import os
from contextlib import suppress
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from market_monitor_gui.platforms import ensure_data_dir

logger = logging.getLogger(__name__)

KEY_FILENAME = "secret.key"
SECRET_FILENAME = "secret.enc"

_FILE_MODE = 0o600
_DIR_MODE = 0o700


class SecretStoreError(RuntimeError):
    """Raised when the store cannot be written safely (e.g. a corrupt key file)."""


class SecretStore:
    """Store and retrieve the application secret in encrypted form."""

    def __init__(self, directory: str | Path) -> None:
        self._directory = Path(directory)

    @classmethod
    def in_data_dir(cls) -> SecretStore:
        return cls(ensure_data_dir())

    @property
    def directory(self) -> Path:
        return self._directory

    @property
    def key_path(self) -> Path:
        return self._directory / KEY_FILENAME

    @property
    def secret_path(self) -> Path:
        return self._directory / SECRET_FILENAME

    def is_saved(self) -> bool:
        return self.secret_path.is_file()

    def save(self, secret: str) -> None:
        """Encrypt and persist ``secret``, creating the key file on first use."""
        if not secret:
            raise ValueError("refusing to store an empty secret")
        self._ensure_directory()
        fernet = self._fernet(self._load_or_create_key())
        self._write_private(self.secret_path, fernet.encrypt(secret.encode("utf-8")))

    def load(self) -> str | None:
        """Return the stored secret, or ``None`` when absent or undecryptable."""
        try:
            token = self.secret_path.read_bytes()
        except OSError:
            return None
        key = self._read_key()
        if key is None:
            return None
        try:
            return self._fernet(key).decrypt(token).decode("utf-8")
        except InvalidToken, SecretStoreError, ValueError, OSError:
            logger.warning("stored secret could not be decrypted; ignoring it")
            return None

    def clear(self) -> None:
        """Remove the stored secret (the key file is kept for future saves)."""
        with suppress(OSError):
            self.secret_path.unlink()

    def _read_key(self) -> bytes | None:
        try:
            key = self.key_path.read_bytes()
        except OSError:
            return None
        return key or None

    def _load_or_create_key(self) -> bytes:
        existing = self._read_key()
        if existing is not None:
            return existing
        key = Fernet.generate_key()
        self._write_private(self.key_path, key)
        return key

    @staticmethod
    def _fernet(key: bytes) -> Fernet:
        try:
            return Fernet(key)
        except ValueError as exc:
            raise SecretStoreError("secret key file is invalid") from exc

    def _ensure_directory(self) -> None:
        self._directory.mkdir(parents=True, exist_ok=True)
        if os.name != "nt":
            with suppress(OSError):
                self._directory.chmod(_DIR_MODE)

    @staticmethod
    def _write_private(path: Path, data: bytes) -> None:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, _FILE_MODE)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)

    def __repr__(self) -> str:
        return f"SecretStore(directory={str(self._directory)!r})"
