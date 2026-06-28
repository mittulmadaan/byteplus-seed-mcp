"""BytePlus provider — placeholder until the native Seed Audio API ships.

When BytePlus releases its own Seed Audio endpoint, implement submit()/status()
here against it and set SEED_PROVIDER=byteplus (or flip DEFAULT_PROVIDER in
config.py). No other layer — client, MCP, CLI, skill — needs to change.
"""
from __future__ import annotations

from ..credentials import credentials_configured
from ..exceptions import ProviderError
from ..types import AudioParams, TaskResult
from .base import AudioProvider

_NOT_READY = (
    "The BytePlus Seed Audio API is not yet available. "
    "Seed Audio currently runs on fal.ai — set SEED_PROVIDER=fal (the default) "
    "and configure FAL_KEY."
)


class BytePlusProvider(AudioProvider):
    name = "byteplus"

    def __init__(self, api_key: str | None = None, *, profile: str = "default") -> None:
        self._explicit_key = api_key
        self._profile = profile

    def configured(self) -> bool:
        return credentials_configured(profile=self._profile)["byteplus_seed_api_key"]

    def submit(self, params: AudioParams) -> TaskResult:
        raise ProviderError(_NOT_READY)

    def status(self, request_id: str) -> TaskResult:
        raise ProviderError(_NOT_READY)
