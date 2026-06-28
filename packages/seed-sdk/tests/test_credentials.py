"""Tests for the credential resolution chain."""
from __future__ import annotations

import pytest

from seed.credentials import (
    clear_credentials,
    credentials_configured,
    load_byteplus_auth,
    load_fal_key,
    write_credentials,
)
from seed.exceptions import AuthError


@pytest.fixture(autouse=True)
def isolate_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr("seed.credentials.CREDENTIALS_PATH", tmp_path / "credentials")
    monkeypatch.delenv("FAL_KEY", raising=False)
    monkeypatch.delenv("BYTEPLUS_SEED_API_KEY", raising=False)
    monkeypatch.delenv("BYTEPLUS_SEED_APP_ID", raising=False)
    monkeypatch.delenv("BYTEPLUS_SEED_ACCESS_KEY", raising=False)


def test_explicit_key_wins():
    assert load_fal_key("explicit-key") == "explicit-key"


def test_env_var_resolves(monkeypatch):
    monkeypatch.setenv("FAL_KEY", "env-key")
    assert load_fal_key() == "env-key"


def test_missing_key_raises():
    with pytest.raises(AuthError, match="FAL_KEY"):
        load_fal_key()


def test_write_and_read_roundtrip():
    write_credentials("file-key")
    assert load_fal_key() == "file-key"
    assert credentials_configured()["fal_key"] is True


def test_clear_credentials():
    write_credentials("file-key")
    assert clear_credentials() is True
    assert credentials_configured()["fal_key"] is False


def test_byteplus_api_key_header(monkeypatch):
    monkeypatch.setenv("BYTEPLUS_SEED_API_KEY", "bp-key")
    assert load_byteplus_auth() == {"X-Api-Key": "bp-key"}


def test_byteplus_legacy_headers(monkeypatch):
    monkeypatch.setenv("BYTEPLUS_SEED_APP_ID", "app1")
    monkeypatch.setenv("BYTEPLUS_SEED_ACCESS_KEY", "ak1")
    assert load_byteplus_auth() == {"X-Api-App-Id": "app1", "X-Api-Access-Key": "ak1"}


def test_byteplus_api_key_takes_precedence(monkeypatch):
    monkeypatch.setenv("BYTEPLUS_SEED_API_KEY", "bp-key")
    monkeypatch.setenv("BYTEPLUS_SEED_APP_ID", "app1")
    monkeypatch.setenv("BYTEPLUS_SEED_ACCESS_KEY", "ak1")
    assert load_byteplus_auth() == {"X-Api-Key": "bp-key"}


def test_byteplus_missing_raises():
    with pytest.raises(AuthError, match="BytePlus"):
        load_byteplus_auth()


def test_byteplus_credentials_roundtrip():
    write_credentials(byteplus_seed_api_key="bp-file-key")
    assert load_byteplus_auth() == {"X-Api-Key": "bp-file-key"}
    cfg = credentials_configured()
    assert cfg["byteplus_seed_api_key"] is True
