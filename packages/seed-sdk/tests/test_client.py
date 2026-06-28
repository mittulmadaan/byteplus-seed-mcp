"""Tests for SeedClient — HTTP mocked at the provider's request_with_retry boundary."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from seed import SeedClient
from seed.exceptions import ValidationError


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("FAL_KEY", "test-fal-key")
    return SeedClient()


def _patch_http(responses):
    """Patch request_with_retry in fal.py to return queued responses in order."""
    return patch("seed.providers.fal.request_with_retry", side_effect=responses)


def _payload_of(mock, call_index=0):
    return mock.call_args_list[call_index].kwargs.get("payload")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_empty_prompt_raises(client):
    with pytest.raises(ValidationError, match="prompt"):
        client.submit_audio("")


def test_invalid_output_format_raises(client):
    with pytest.raises(ValidationError, match="output_format"):
        client.submit_audio("hi", output_format="flac")


def test_invalid_sample_rate_raises(client):
    with pytest.raises(ValidationError, match="sample_rate"):
        client.submit_audio("hi", sample_rate=12345)


def test_audio_and_image_mutually_exclusive(client):
    with pytest.raises(ValidationError, match="mutually exclusive"):
        client.submit_audio(
            "hi",
            audio_urls=["https://example.com/a.mp3"],
            image_url="https://example.com/i.png",
        )


def test_too_many_audio_refs_raises(client):
    with pytest.raises(ValidationError, match="Too many audio_urls"):
        client.submit_audio(
            "hi", audio_urls=[f"https://example.com/{i}.mp3" for i in range(4)]
        )


def test_pitch_out_of_range_raises(client):
    with pytest.raises(ValidationError, match="pitch"):
        client.submit_audio("hi", pitch=24)


# ---------------------------------------------------------------------------
# Submit
# ---------------------------------------------------------------------------

def test_submit_returns_request_id(client):
    with _patch_http([{"request_id": "req-123", "status": "IN_QUEUE"}]):
        result = client.submit_audio("A suspense radio drama.")
    assert result.request_id == "req-123"
    assert result.status == "queued"
    assert result.provider == "fal"


def test_submit_builds_input_payload(client):
    with _patch_http([{"request_id": "req-1", "status": "IN_QUEUE"}]) as mock:
        client.submit_audio(
            "Hello world",
            voice="sophie_en_zh",
            speed=1.5,
            output_format="wav",
        )
    payload = _payload_of(mock)
    assert payload["prompt"] == "Hello world"
    assert payload["voice"] == "sophie_en_zh"
    assert payload["speed"] == 1.5
    assert payload["output_format"] == "wav"


def test_submit_omits_unset_optionals(client):
    with _patch_http([{"request_id": "req-1", "status": "IN_QUEUE"}]) as mock:
        client.submit_audio("Hello")
    payload = _payload_of(mock)
    assert "voice" not in payload
    assert "image_url" not in payload
    assert "audio_urls" not in payload
    assert "pitch" not in payload


# ---------------------------------------------------------------------------
# Poll
# ---------------------------------------------------------------------------

def test_check_task_completed_fetches_audio_url(client):
    responses = [
        {"status": "COMPLETED"},
        {"audio": {"url": "https://cdn.fal.ai/out.mp3", "duration": 12.3}},
    ]
    with _patch_http(responses):
        result = client.check_task("req-123")
    assert result.succeeded
    assert result.audio_url == "https://cdn.fal.ai/out.mp3"
    assert result.audio["duration"] == 12.3


def test_check_task_running(client):
    with _patch_http([{"status": "IN_PROGRESS"}]):
        result = client.check_task("req-running")
    assert not result.terminal
    assert result.audio_url is None


def test_check_task_failed(client):
    with _patch_http([{"status": "FAILED", "error": "bad input"}]):
        result = client.check_task("req-bad")
    assert result.terminal
    assert not result.succeeded


def test_check_task_requires_id(client):
    with pytest.raises(ValidationError, match="request_id"):
        client.check_task("")


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

def test_list_voices(client):
    data = client.list_voices()
    assert "sophie_en_zh" in data["voices"]
    assert data["count"] == len(data["voices"])


def test_list_models_includes_seed_audio(client):
    data = client.list_models()
    ids = [m["model_id"] for m in data["models"]]
    assert "seed-audio-1.0" in ids


def test_ping_reports_provider_and_version(client, monkeypatch, tmp_path):
    monkeypatch.setattr("seed.credentials.CREDENTIALS_PATH", tmp_path / "credentials")
    result = client.ping()
    assert result["status"] == "ok"
    assert result["provider"] == "fal"
    assert "version" in result


# ---------------------------------------------------------------------------
# BytePlus provider (synchronous) via the client
# ---------------------------------------------------------------------------

def test_byteplus_submit_returns_completed(monkeypatch):
    monkeypatch.setenv("BYTEPLUS_SEED_API_KEY", "bp-key")
    client = SeedClient(provider="byteplus")
    resp = {"code": 0, "url": "https://x/out.mp3", "duration": 4.0, "audio": "QUJD"}
    with patch("seed.providers.byteplus.request_with_retry", return_value=resp):
        result = client.submit_audio("A late-night radio drama.")
    # Synchronous: no polling needed — audio is already here.
    assert result.succeeded
    assert result.audio_url == "https://x/out.mp3"
    assert result.provider == "byteplus"


def test_byteplus_check_task_is_synchronous_error(monkeypatch):
    from seed.exceptions import ProviderError
    monkeypatch.setenv("BYTEPLUS_SEED_API_KEY", "bp-key")
    client = SeedClient(provider="byteplus")
    with pytest.raises(ProviderError, match="synchronous"):
        client.check_task("some-id")


def test_provider_override_beats_env(monkeypatch):
    monkeypatch.setenv("SEED_PROVIDER", "byteplus")
    monkeypatch.setenv("FAL_KEY", "fk")
    client = SeedClient(provider="fal")
    assert client.ping()["provider"] == "fal"
