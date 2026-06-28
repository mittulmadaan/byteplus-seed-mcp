"""Provider interface — every audio backend implements this contract."""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..types import AudioParams, TaskResult


class AudioProvider(ABC):
    """Abstract audio backend.

    Implementations encapsulate all transport, auth, and response-shape
    specifics so that SeedClient, the MCP server, and the CLI never have to
    know which backend is in use.
    """

    #: short provider name, e.g. "fal" — surfaced in TaskResult.provider
    name: str = "base"

    @abstractmethod
    def submit(self, params: AudioParams) -> TaskResult:
        """Submit an audio job and return a TaskResult carrying request_id."""

    @abstractmethod
    def status(self, request_id: str) -> TaskResult:
        """Poll a job. When complete, the TaskResult includes audio_url."""

    @abstractmethod
    def configured(self) -> bool:
        """Return True when credentials for this provider are available."""
