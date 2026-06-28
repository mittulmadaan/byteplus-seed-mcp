"""BytePlus / Volcengine Doubao provider for Seed Audio 1.0.

The BytePlus Audio Generation HTTP API is **synchronous**: a single
``POST /api/v3/tts/create`` returns the generated audio (Base64 + a temporary
2-hour URL). There is no task to poll — so ``submit()`` returns a already-
``completed`` TaskResult and ``status()`` is not applicable.

Docs: https://www.volcengine.com/docs/6561/2550782

Wire-format differences from fal (handled here, hidden from the rest of the SDK):
  - ``prompt``        -> ``text_prompt``
  - ``voice``         -> a ``{"speaker": ...}`` item in ``references``
  - ``audio_urls``    -> ``[{"audio_url": ...}, ...]`` in ``references``
  - ``image_url``     -> ``[{"image_url": ...}]`` in ``references``
  - ``output_format`` -> ``audio_config.format``
  - ``sample_rate``   -> ``audio_config.sample_rate``
  - ``speed`` (float) -> ``audio_config.speech_rate``  (int, -50..100)
  - ``volume`` (float)-> ``audio_config.loudness_rate`` (int, -50..100)
  - ``pitch`` (int)   -> ``audio_config.pitch_rate``    (int, -12..12)
"""
from __future__ import annotations

import uuid
from typing import Any

from ..config import (
    BYTEPLUS_MODEL,
    BYTEPLUS_PROMPT_MAXLEN,
    BYTEPLUS_TTS_URL,
    RATE_MAX,
    RATE_MIN,
    SUBMIT_TIMEOUT,
)
from ..credentials import credentials_configured, load_byteplus_auth
from ..exceptions import APIError, ProviderError, ValidationError
from ..http import request_with_retry
from ..types import AudioParams, TaskResult
from .base import AudioProvider


def _rate(multiplier: float) -> int:
    """Map a fal-style multiplier (1.0 = normal) to a BytePlus rate int.

    BytePlus uses ints in [-50, 100] where 100 = 2.0x and -50 = 0.5x — i.e.
    rate = (multiplier - 1.0) * 100, clamped.
    """
    return max(RATE_MIN, min(RATE_MAX, round((multiplier - 1.0) * 100)))


class BytePlusProvider(AudioProvider):
    name = "byteplus"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        app_id: str | None = None,
        access_key: str | None = None,
        profile: str = "default",
    ) -> None:
        self._explicit_key = api_key
        self._explicit_app_id = app_id
        self._explicit_access_key = access_key
        self._profile = profile

    # -- auth -------------------------------------------------------------
    def _auth_headers(self) -> dict[str, str]:
        return load_byteplus_auth(
            self._explicit_key,
            self._explicit_app_id,
            self._explicit_access_key,
            profile=self._profile,
        )

    def configured(self) -> bool:
        c = credentials_configured(profile=self._profile)
        return c["byteplus_seed_api_key"] or (
            c["byteplus_seed_app_id"] and c["byteplus_seed_access_key"]
        )

    # -- payload ----------------------------------------------------------
    def build_payload(self, params: AudioParams) -> dict[str, Any]:
        references: list[dict[str, str]] = []
        if params.voice:
            references.append({"speaker": params.voice})
        if params.audio_urls:
            references.extend({"audio_url": u} for u in params.audio_urls)
        if params.image_url:
            references.append({"image_url": params.image_url})

        payload: dict[str, Any] = {
            "model": BYTEPLUS_MODEL,
            "text_prompt": params.prompt,
            "audio_config": {
                "format": params.output_format,
                "sample_rate": params.sample_rate,
                "speech_rate": _rate(params.speed),
                "loudness_rate": _rate(params.volume),
                "pitch_rate": params.pitch or 0,
            },
            "watermark": {},
        }
        if references:
            payload["references"] = references
        return payload

    # -- API --------------------------------------------------------------
    def submit(self, params: AudioParams) -> TaskResult:
        params.validate()
        if len(params.prompt) > BYTEPLUS_PROMPT_MAXLEN:
            raise ValidationError(
                f"text_prompt exceeds BytePlus limit of {BYTEPLUS_PROMPT_MAXLEN} "
                f"characters ({len(params.prompt)}). Split long scripts into chunks."
            )

        request_id = str(uuid.uuid4())
        headers = {
            "Content-Type": "application/json",
            "X-Api-Request-Id": request_id,
            **self._auth_headers(),
        }
        resp = request_with_retry(
            BYTEPLUS_TTS_URL,
            method="POST",
            headers=headers,
            payload=self.build_payload(params),
            timeout=SUBMIT_TIMEOUT,
        )

        audio_url = resp.get("url") or None
        has_base64 = bool(resp.get("audio"))
        if not audio_url and not has_base64:
            raise APIError(
                f"BytePlus error {resp.get('code')}: {resp.get('message', 'unknown error')}"
            )

        audio = {
            "url": audio_url,
            "duration": resp.get("duration"),
            "original_duration": resp.get("original_duration"),
            "has_base64": has_base64,
        }
        return TaskResult(
            request_id=request_id,
            status="completed",
            audio_url=audio_url,
            audio=audio,
            provider=self.name,
            raw=resp,
        )

    def status(self, request_id: str) -> TaskResult:
        raise ProviderError(
            "BytePlus Seed Audio is synchronous — the audio is returned directly by "
            "submit_audio(); there is no task to poll. Read audio_url from the submit result."
        )
