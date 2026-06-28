"""Typed exceptions for the Seed SDK."""
from __future__ import annotations


class SeedError(Exception):
    """Base exception for all Seed SDK errors."""


class AuthError(SeedError):
    """Raised when credentials are missing or invalid."""


class ValidationError(SeedError):
    """Raised when request parameters fail validation."""


class APIError(SeedError):
    """Raised when a provider API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ProviderError(SeedError):
    """Raised when a provider is unknown or not yet available."""


class TimeoutError(SeedError):
    """Raised when polling exceeds the configured deadline."""
