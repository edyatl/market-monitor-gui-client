"""G3: encrypted secret store (Fernet)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from market_monitor_gui.config.secret_store import (
    KEY_FILENAME,
    SECRET_FILENAME,
    SecretStore,
    SecretStoreError,
)
from market_monitor_gui.platforms import _constants

pytestmark = pytest.mark.unit

SECRET = "shared-app-secret-value"

posix_only = pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")


def test_round_trip(tmp_path: Path) -> None:
    store = SecretStore(tmp_path)
    assert store.is_saved() is False
    store.save(SECRET)
    assert store.is_saved() is True
    assert store.load() == SECRET


def test_ciphertext_does_not_contain_plaintext(tmp_path: Path) -> None:
    store = SecretStore(tmp_path)
    store.save(SECRET)
    on_disk = store.secret_path.read_bytes()
    assert SECRET.encode("utf-8") not in on_disk
    assert SECRET not in store.key_path.read_bytes().decode("latin-1")


def test_files_use_expected_names(tmp_path: Path) -> None:
    store = SecretStore(tmp_path)
    store.save(SECRET)
    assert store.key_path.name == KEY_FILENAME
    assert store.secret_path.name == SECRET_FILENAME
    assert store.key_path.is_file()
    assert store.secret_path.is_file()


@posix_only
def test_key_and_secret_files_are_private(tmp_path: Path) -> None:
    store = SecretStore(tmp_path / "data")
    store.save(SECRET)
    assert store.key_path.stat().st_mode & 0o777 == 0o600
    assert store.secret_path.stat().st_mode & 0o777 == 0o600
    assert store.directory.stat().st_mode & 0o777 == 0o700


def test_load_missing_returns_none(tmp_path: Path) -> None:
    assert SecretStore(tmp_path).load() is None


def test_clear_removes_secret_but_keeps_key(tmp_path: Path) -> None:
    store = SecretStore(tmp_path)
    store.save(SECRET)
    store.clear()
    assert store.is_saved() is False
    assert store.load() is None
    assert store.key_path.is_file()
    store.clear()  # idempotent


def test_wrong_key_returns_none(tmp_path: Path) -> None:
    store = SecretStore(tmp_path)
    store.save(SECRET)
    store.key_path.write_bytes(Fernet.generate_key())
    assert store.load() is None


def test_corrupt_key_returns_none_on_load(tmp_path: Path) -> None:
    store = SecretStore(tmp_path)
    store.save(SECRET)
    store.key_path.write_bytes(b"not-a-valid-key")
    assert store.load() is None


def test_corrupt_key_raises_on_save(tmp_path: Path) -> None:
    store = SecretStore(tmp_path)
    store.save(SECRET)
    store.key_path.write_bytes(b"not-a-valid-key")
    with pytest.raises(SecretStoreError):
        store.save(SECRET)


def test_empty_secret_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        SecretStore(tmp_path).save("")


def test_repr_never_contains_secret(tmp_path: Path) -> None:
    store = SecretStore(tmp_path)
    store.save(SECRET)
    assert SECRET not in repr(store)
    assert SECRET not in str(store.directory)


def test_second_save_reuses_key(tmp_path: Path) -> None:
    store = SecretStore(tmp_path)
    store.save(SECRET)
    key_before = store.key_path.read_bytes()
    store.save("another-secret")
    assert store.key_path.read_bytes() == key_before
    assert store.load() == "another-secret"


def test_in_data_dir_uses_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(_constants.DATA_DIR_ENV, str(tmp_path / "data"))
    store = SecretStore.in_data_dir()
    assert store.directory == tmp_path / "data"
