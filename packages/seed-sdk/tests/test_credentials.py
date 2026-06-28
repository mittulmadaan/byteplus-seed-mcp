"""Tests for the credential resolution chain."""
from __future__ import annotations

import pytest

from seed import SeedClient
from seed.credentials import (
    clear_credentials,
    credentials_configured,
    load_fal_key,
    write_credentials,
)
from seed.exceptions import AuthError, ProviderError


@pytest.fixture(autouse=True)
def isolate_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr("seed.credentials.CREDENTIALS_PATH", tmp_path / "credentials")
    monkeypatch.delenv("FAL_KEY", raising=False)
    monkeypatch.delenv("BYTEPLUS_SEED_API_KEY", raising=False)


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


def test_byteplus_provider_not_ready(monkeypatch):
    monkeypatch.setenv("FAL_KEY", "x")
    client = SeedClient(provider="byteplus")
    with pytest.raises(ProviderError, match="not yet available"):
        client.submit_audio("hello")
