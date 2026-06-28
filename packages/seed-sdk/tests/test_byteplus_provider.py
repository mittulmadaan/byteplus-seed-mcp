"""Tests for the BytePlus (Volcengine Doubao) synchronous provider."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from seed.exceptions import APIError, AuthError, ProviderError, ValidationError
from seed.providers.byteplus import BytePlusProvider, _rate
from seed.types import AudioParams

_OK = {"code": 0, "message": "ok", "url": "https://x/out.mp3", "duration": 3.5, "audio": "QUJD"}


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv("BYTEPLUS_SEED_API_KEY", "bp-key")
    monkeypatch.delenv("BYTEPLUS_SEED_APP_ID", raising=False)
    monkeypatch.delenv("BYTEPLUS_SEED_ACCESS_KEY", raising=False)
    return BytePlusProvider()


def _payload(mock):
    return mock.call_args.kwargs["payload"]


def _headers(mock):
    return mock.call_args.kwargs["headers"]


# ---------------------------------------------------------------------------
# Rate conversion (fal multiplier -> BytePlus int [-50, 100])
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mult,expected", [(1.0, 0), (2.0, 100), (0.5, -50), (1.5, 50), (3.0, 100), (0.1, -50)])
def test_rate_conversion(mult, expected):
    assert _rate(mult) == expected


# ---------------------------------------------------------------------------
# Endpoint, auth, payload shape
# ---------------------------------------------------------------------------

def test_submit_url_and_api_key_header(provider):
    with patch("seed.providers.byteplus.request_with_retry", return_value=_OK) as mock:
        provider.submit(AudioParams(prompt="hi"))
    assert mock.call_args.args[0].endswith("/api/v3/tts/create")
    h = _headers(mock)
    assert h["X-Api-Key"] == "bp-key"
    assert "X-Api-Request-Id" in h


def test_legacy_app_id_access_key_headers(monkeypatch):
    monkeypatch.delenv("BYTEPLUS_SEED_API_KEY", raising=False)
    monkeypatch.setenv("BYTEPLUS_SEED_APP_ID", "app1")
    monkeypatch.setenv("BYTEPLUS_SEED_ACCESS_KEY", "ak1")
    prov = BytePlusProvider()
    with patch("seed.providers.byteplus.request_with_retry", return_value=_OK) as mock:
        prov.submit(AudioParams(prompt="hi"))
    h = _headers(mock)
    assert h["X-Api-App-Id"] == "app1"
    assert h["X-Api-Access-Key"] == "ak1"
    assert "X-Api-Key" not in h


def test_missing_credentials_raises(monkeypatch, tmp_path):
    monkeypatch.delenv("BYTEPLUS_SEED_API_KEY", raising=False)
    monkeypatch.delenv("BYTEPLUS_SEED_APP_ID", raising=False)
    monkeypatch.delenv("BYTEPLUS_SEED_ACCESS_KEY", raising=False)
    monkeypatch.setattr("seed.credentials.CREDENTIALS_PATH", tmp_path / "credentials")
    with pytest.raises(AuthError, match="BytePlus"):
        BytePlusProvider().submit(AudioParams(prompt="hi"))


def test_payload_field_mapping(provider):
    with patch("seed.providers.byteplus.request_with_retry", return_value=_OK) as mock:
        provider.submit(AudioParams(
            prompt="Read @Audio1.", output_format="mp3", sample_rate=48000,
            speed=2.0, volume=0.5, pitch=3,
        ))
    p = _payload(mock)
    assert p["model"] == "seed-audio-1.0"
    assert p["text_prompt"] == "Read @Audio1."
    assert p["audio_config"] == {
        "format": "mp3", "sample_rate": 48000,
        "speech_rate": 100, "loudness_rate": -50, "pitch_rate": 3,
    }
    assert p["watermark"] == {}


def test_voice_becomes_speaker_reference(provider):
    with patch("seed.providers.byteplus.request_with_retry", return_value=_OK) as mock:
        provider.submit(AudioParams(prompt="hi", voice="zh_female_x"))
    assert _payload(mock)["references"] == [{"speaker": "zh_female_x"}]


def test_audio_urls_become_references(provider):
    with patch("seed.providers.byteplus.request_with_retry", return_value=_OK) as mock:
        provider.submit(AudioParams(prompt="@Audio1 @Audio2", audio_urls=["u1", "u2"]))
    assert _payload(mock)["references"] == [{"audio_url": "u1"}, {"audio_url": "u2"}]


def test_image_url_becomes_reference(provider):
    with patch("seed.providers.byteplus.request_with_retry", return_value=_OK) as mock:
        provider.submit(AudioParams(prompt="describe", image_url="https://x/i.png"))
    assert _payload(mock)["references"] == [{"image_url": "https://x/i.png"}]


def test_text_only_omits_references(provider):
    with patch("seed.providers.byteplus.request_with_retry", return_value=_OK) as mock:
        provider.submit(AudioParams(prompt="hi"))
    assert "references" not in _payload(mock)


# ---------------------------------------------------------------------------
# Response handling (synchronous: submit returns completed)
# ---------------------------------------------------------------------------

def test_submit_returns_completed_with_audio_url(provider):
    with patch("seed.providers.byteplus.request_with_retry", return_value=_OK):
        result = provider.submit(AudioParams(prompt="hi"))
    assert result.succeeded
    assert result.terminal
    assert result.audio_url == "https://x/out.mp3"
    assert result.audio["duration"] == 3.5
    assert result.audio["has_base64"] is True
    assert result.provider == "byteplus"


def test_submit_error_when_no_audio(provider):
    with patch("seed.providers.byteplus.request_with_retry",
               return_value={"code": 40001, "message": "bad voice"}), \
         pytest.raises(APIError, match="40001"):
        provider.submit(AudioParams(prompt="hi"))


def test_prompt_too_long_raises(provider):
    with pytest.raises(ValidationError, match="exceeds BytePlus limit"):
        provider.submit(AudioParams(prompt="x" * 2049))


def test_status_raises_synchronous(provider):
    with pytest.raises(ProviderError, match="synchronous"):
        provider.status("anything")
