"""Audio providers — swap the backend without touching the client surface."""
from __future__ import annotations

from ..config import DEFAULT_PROVIDER, PROVIDERS
from ..exceptions import ProviderError
from .base import AudioProvider
from .byteplus import BytePlusProvider
from .fal import FalProvider


def get_provider(
    name: str | None = None,
    *,
    fal_key: str | None = None,
    byteplus_key: str | None = None,
    byteplus_app_id: str | None = None,
    byteplus_access_key: str | None = None,
    profile: str = "default",
) -> AudioProvider:
    """Construct the provider for `name` (defaults to SEED_PROVIDER / 'fal')."""
    chosen = (name or DEFAULT_PROVIDER).strip().lower()
    if chosen not in PROVIDERS:
        raise ProviderError(
            f"Unknown provider '{chosen}'. Available: {', '.join(sorted(PROVIDERS))}."
        )
    if chosen == "fal":
        return FalProvider(api_key=fal_key, profile=profile)
    return BytePlusProvider(
        api_key=byteplus_key,
        app_id=byteplus_app_id,
        access_key=byteplus_access_key,
        profile=profile,
    )


__all__ = ["AudioProvider", "FalProvider", "BytePlusProvider", "get_provider"]
