"""Credential loading with a priority chain.

Resolution order (first non-empty value wins):
  1. Explicit constructor arguments
  2. Environment variables  (FAL_KEY)
  3. ~/.seed/credentials  INI file  [default] section
  4. .env file in CWD  (loaded only when python-dotenv is installed)

When the BytePlus Seed API ships, BYTEPLUS_SEED_API_KEY slots into the same
chain — the labelled helper below is already wired for it.
"""
from __future__ import annotations

import configparser
import os
from pathlib import Path

from .exceptions import AuthError

CREDENTIALS_PATH = Path.home() / ".seed" / "credentials"
CONFIG_PATH = Path.home() / ".seed" / "config"


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def _read_ini(path: Path, section: str, key: str) -> str:
    if not path.exists():
        return ""
    parser = configparser.ConfigParser()
    parser.read(path)
    return parser.get(section, key, fallback="").strip()


def load_fal_key(explicit: str | None = None, *, profile: str = "default") -> str:
    """Return the fal.ai API key, or raise AuthError."""
    _load_dotenv()

    value = (
        (explicit or "").strip()
        or os.getenv("FAL_KEY", "").strip()
        or _read_ini(CREDENTIALS_PATH, profile, "fal_key")
    )

    if not value:
        raise AuthError(
            "FAL_KEY is not configured.\n"
            "Seed Audio currently runs on fal.ai. Set the key via one of:\n"
            "  export FAL_KEY=<key>\n"
            "  seed auth login\n"
            "  echo '[default]\\nfal_key=<key>' > ~/.seed/credentials\n"
            "Get a key at https://fal.ai/dashboard/keys"
        )
    return value


def load_byteplus_key(explicit: str | None = None, *, profile: str = "default") -> str:
    """Return the BytePlus Seed API key, or raise AuthError.

    Reserved for when BytePlus releases its own Seed Audio API.
    """
    _load_dotenv()

    value = (
        (explicit or "").strip()
        or os.getenv("BYTEPLUS_SEED_API_KEY", "").strip()
        or _read_ini(CREDENTIALS_PATH, profile, "byteplus_seed_api_key")
    )

    if not value:
        raise AuthError(
            "BYTEPLUS_SEED_API_KEY is not configured.\n"
            "Set it via 'export BYTEPLUS_SEED_API_KEY=<key>' or 'seed auth login'."
        )
    return value


def write_credentials(
    fal_key: str,
    *,
    byteplus_seed_api_key: str = "",
    profile: str = "default",
) -> None:
    """Persist credentials to ~/.seed/credentials."""
    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)

    parser = configparser.ConfigParser()
    if CREDENTIALS_PATH.exists():
        parser.read(CREDENTIALS_PATH)

    if not parser.has_section(profile):
        parser.add_section(profile)

    if fal_key:
        parser.set(profile, "fal_key", fal_key)
    if byteplus_seed_api_key:
        parser.set(profile, "byteplus_seed_api_key", byteplus_seed_api_key)

    with CREDENTIALS_PATH.open("w") as f:
        parser.write(f)

    # Restrict permissions — credentials file should not be world-readable
    CREDENTIALS_PATH.chmod(0o600)


def clear_credentials(*, profile: str = "default") -> bool:
    """Remove a profile from ~/.seed/credentials. Returns True if file existed."""
    if not CREDENTIALS_PATH.exists():
        return False

    parser = configparser.ConfigParser()
    parser.read(CREDENTIALS_PATH)

    if parser.has_section(profile):
        parser.remove_section(profile)
        with CREDENTIALS_PATH.open("w") as f:
            parser.write(f)

    return True


def credentials_configured(*, profile: str = "default") -> dict[str, bool]:
    """Return which credentials are available (for `seed auth check`)."""
    _load_dotenv()
    return {
        "fal_key": bool(
            os.getenv("FAL_KEY", "").strip()
            or _read_ini(CREDENTIALS_PATH, profile, "fal_key")
        ),
        "byteplus_seed_api_key": bool(
            os.getenv("BYTEPLUS_SEED_API_KEY", "").strip()
            or _read_ini(CREDENTIALS_PATH, profile, "byteplus_seed_api_key")
        ),
    }
