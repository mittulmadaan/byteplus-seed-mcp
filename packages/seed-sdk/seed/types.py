"""Typed parameter and result dataclasses for the Seed SDK."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import (
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_SAMPLE_RATE,
    MAX_REFERENCE_AUDIO,
    OUTPUT_FORMATS,
    SAMPLE_RATES,
)
from .exceptions import ValidationError


@dataclass
class AudioParams:
    """Validated inputs for a Seed Audio generation request.

    Maps 1:1 onto the fal `bytedance/seed-audio-1.0` input schema. Provider
    implementations turn this into their own wire format via `to_input()`.
    """
    prompt: str
    voice: str | None = None
    audio_urls: list[str] | None = None
    image_url: str | None = None
    output_format: str = DEFAULT_OUTPUT_FORMAT
    sample_rate: int = DEFAULT_SAMPLE_RATE
    speed: float = 1.0
    volume: float = 1.0
    pitch: int | None = None

    def validate(self) -> None:
        if not self.prompt or not self.prompt.strip():
            raise ValidationError("prompt is required and cannot be empty.")

        if self.output_format not in OUTPUT_FORMATS:
            raise ValidationError(
                f"Invalid output_format '{self.output_format}'. "
                f"Choose one of: {', '.join(sorted(OUTPUT_FORMATS))}."
            )

        if self.sample_rate not in SAMPLE_RATES:
            raise ValidationError(
                f"Invalid sample_rate {self.sample_rate}. "
                f"Choose one of: {', '.join(str(s) for s in sorted(SAMPLE_RATES))}."
            )

        if self.audio_urls and self.image_url:
            raise ValidationError(
                "audio_urls and image_url are mutually exclusive — pass one or the other."
            )

        if self.audio_urls:
            if len(self.audio_urls) > MAX_REFERENCE_AUDIO:
                raise ValidationError(
                    f"Too many audio_urls ({len(self.audio_urls)}); "
                    f"max is {MAX_REFERENCE_AUDIO}. Reference them as @Audio1..@Audio3."
                )
            if any(not u or not u.strip() for u in self.audio_urls):
                raise ValidationError("audio_urls contains an empty entry.")

        if self.speed <= 0:
            raise ValidationError("speed must be greater than 0.")
        if self.volume <= 0:
            raise ValidationError("volume must be greater than 0.")

    def to_input(self) -> dict[str, Any]:
        """Build the provider `input` payload, omitting unset optional fields."""
        out: dict[str, Any] = {
            "prompt": self.prompt,
            "output_format": self.output_format,
            "sample_rate": self.sample_rate,
            "speed": self.speed,
            "volume": self.volume,
        }
        if self.voice:
            out["voice"] = self.voice
        if self.audio_urls:
            out["audio_urls"] = list(self.audio_urls)
        if self.image_url:
            out["image_url"] = self.image_url
        if self.pitch is not None:
            out["pitch"] = self.pitch
        return out


@dataclass
class TaskResult:
    """Normalised result of submitting or polling an audio task.

    `status` uses the SDK's normalised vocabulary (queued | running | completed
    | failed), not a provider's raw enum.
    """
    request_id: str
    status: str
    audio_url: str | None = None
    audio: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    provider: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"request_id": self.request_id, "status": self.status}
        if self.audio_url:
            out["audio_url"] = self.audio_url
        if self.audio:
            out["audio"] = self.audio
        if self.error:
            out["error"] = self.error
        if self.provider:
            out["provider"] = self.provider
        return out

    @property
    def succeeded(self) -> bool:
        return self.status == "completed"

    @property
    def terminal(self) -> bool:
        return self.status in {"completed", "failed"}
