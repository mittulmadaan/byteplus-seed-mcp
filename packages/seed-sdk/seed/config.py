"""SDK-wide constants, provider endpoints, and the model/voice registry."""
from __future__ import annotations

import os
from typing import Any

__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------------
# Today Seed Audio runs on fal.ai. When BytePlus ships its own API, set
# SEED_PROVIDER=byteplus (or flip DEFAULT_PROVIDER) — nothing else changes.
DEFAULT_PROVIDER = os.getenv("SEED_PROVIDER", "fal").strip().lower()
PROVIDERS: frozenset[str] = frozenset({"fal", "byteplus"})

# ---------------------------------------------------------------------------
# fal.ai queue API  (https://docs.fal.ai/model-endpoints/queue)
# ---------------------------------------------------------------------------
FAL_QUEUE_BASE = os.getenv("SEED_FAL_QUEUE_BASE", "https://queue.fal.run")
FAL_MODEL = "bytedance/seed-audio-1.0"

# ---------------------------------------------------------------------------
# BytePlus / Volcengine Doubao Audio Generation HTTP API
# (https://www.volcengine.com/docs/6561/2550782) — SYNCHRONOUS: one POST returns
# the audio (base64 + a temporary 2h URL); there is no task to poll.
# ---------------------------------------------------------------------------
BYTEPLUS_TTS_URL = os.getenv(
    "SEED_BYTEPLUS_TTS_URL", "https://openspeech.bytedance.com/api/v3/tts/create"
)
BYTEPLUS_MODEL = "seed-audio-1.0"
BYTEPLUS_PROMPT_MAXLEN = 2048
BYTEPLUS_OUTPUT_MAX_SECONDS = 120
# BytePlus speech_rate / loudness_rate are ints in [-50, 100] (100 = 2.0x, -50 = 0.5x).
RATE_MIN, RATE_MAX = -50, 100

# ---------------------------------------------------------------------------
# HTTP tuning (shared across providers)
# ---------------------------------------------------------------------------
SUBMIT_TIMEOUT = int(os.getenv("SEED_SUBMIT_TIMEOUT", "30"))
POLL_TIMEOUT = int(os.getenv("SEED_POLL_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("SEED_MAX_RETRIES", "3"))
INCLUDE_RAW = os.getenv("SEED_DEBUG_RAW", "").lower() in ("1", "true", "yes")

# Normalised task statuses (provider statuses are mapped onto these).
TERMINAL_STATUSES: frozenset[str] = frozenset({"completed", "failed"})

# ---------------------------------------------------------------------------
# Seed Audio 1.0 parameter domains
# ---------------------------------------------------------------------------
OUTPUT_FORMATS: frozenset[str] = frozenset({"mp3", "wav", "pcm", "ogg_opus"})
SAMPLE_RATES: frozenset[int] = frozenset({8000, 16000, 24000, 32000, 44100, 48000})
MAX_REFERENCE_AUDIO = 3
PITCH_MIN, PITCH_MAX = -12, 12

DEFAULT_OUTPUT_FORMAT = "mp3"
DEFAULT_SAMPLE_RATE = 24000

# Preset voices (fal `voice` enum). The model also accepts reference audio
# (voice cloning) via audio_urls, in which case `voice` is omitted.
VOICES: tuple[str, ...] = (
    "vivi_mixed_en_zh_ja_es_id",
    "mindy_en_es_id_pt_zh",
    "kian_en_zh",
    "cedric_en_zh",
    "sophie_en_zh",
    "jean_en_zh",
    "magnus_en_zh",
    "mabel_en_zh",
    "nadia_en_zh",
    "opal_en_zh",
    "pearl_en_zh",
    "quentin_en_zh",
    "corinne_mixed_en_zh",
    "esther_mixed_en_zh",
    "lyla_mixed_en_zh",
    "tracy_es_zh",
    "sandy_es_mixed_en_zh",
    "felix_zh",
    "celeste_zh",
    "monkey_king_zh",
)

# Model capability registry — mirrors seedance's MODELS map so the CLI/MCP can
# advertise capabilities uniformly and new Seed models slot in here.
MODELS: dict[str, dict[str, Any]] = {
    "seed-audio-1.0": {
        "label": "Seed Audio 1.0",
        "alias": "audio",
        "providers": ["fal", "byteplus"],
        "fal_model": FAL_MODEL,
        "byteplus_model": BYTEPLUS_MODEL,
        "kind": "audio",
        "output_formats": sorted(OUTPUT_FORMATS),
        "sample_rates": sorted(SAMPLE_RATES),
        "supports_voice_presets": True,
        "supports_reference_audio": True,
        "supports_reference_image": True,
        "max_reference_audio": MAX_REFERENCE_AUDIO,
    },
}

DEFAULT_MODEL = "seed-audio-1.0"


def model_caps(model: str) -> dict[str, Any]:
    return MODELS.get(model, MODELS[DEFAULT_MODEL])
