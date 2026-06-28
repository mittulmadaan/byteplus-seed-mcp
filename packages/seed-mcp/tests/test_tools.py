"""Smoke tests for MCP tool contracts — verify shape of returned dicts."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from seed.types import TaskResult


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("FAL_KEY", "test-fal-key")


def test_audio_generate_returns_request_id():
    from seed_mcp.server import seed_audio_generate
    mock_result = TaskResult(request_id="req-123", status="queued", provider="fal")
    with patch("seed_mcp.server.SeedClient") as MockClient:
        MockClient.return_value.submit_audio.return_value = mock_result
        result = seed_audio_generate("A suspense radio drama.")
    assert result["request_id"] == "req-123"
    assert result["status"] == "queued"
    assert "message" in result


def test_audio_generate_forwards_voice_and_refs():
    from seed_mcp.server import seed_audio_generate
    mock_result = TaskResult(request_id="req-1", status="queued", provider="fal")
    with patch("seed_mcp.server.SeedClient") as MockClient:
        MockClient.return_value.submit_audio.return_value = mock_result
        seed_audio_generate(
            "She says @Audio1.",
            voice="sophie_en_zh",
            audio_urls=["https://example.com/voice.mp3"],
        )
    kwargs = MockClient.return_value.submit_audio.call_args.kwargs
    assert kwargs["voice"] == "sophie_en_zh"
    assert kwargs["audio_urls"] == ["https://example.com/voice.mp3"]


def test_check_task_completed_has_audio_url():
    from seed_mcp.server import seed_check_task
    mock_result = TaskResult(
        request_id="req-123",
        status="completed",
        audio_url="https://cdn.fal.ai/out.mp3",
    )
    with patch("seed_mcp.server.SeedClient") as MockClient:
        MockClient.return_value.check_task.return_value = mock_result
        result = seed_check_task("req-123")
    assert result["audio_url"] == "https://cdn.fal.ai/out.mp3"
    assert "ready" in result["message"].lower()


def test_check_task_running_has_poll_message():
    from seed_mcp.server import seed_check_task
    mock_result = TaskResult(request_id="req-123", status="running")
    with patch("seed_mcp.server.SeedClient") as MockClient:
        MockClient.return_value.check_task.return_value = mock_result
        result = seed_check_task("req-123")
    assert "processing" in result["message"].lower()


def test_error_from_sdk_returns_error_dict():
    from seed.exceptions import ValidationError
    from seed_mcp.server import seed_audio_generate
    with patch("seed_mcp.server.SeedClient") as MockClient:
        MockClient.return_value.submit_audio.side_effect = ValidationError("bad format")
        result = seed_audio_generate("test", output_format="flac")
    assert result["status"] == "error"
    assert "bad format" in result["error"]


def test_list_voices():
    from seed_mcp.server import seed_list_voices
    with patch("seed_mcp.server.SeedClient") as MockClient:
        MockClient.return_value.list_voices.return_value = {"voices": ["sophie_en_zh"], "count": 1}
        result = seed_list_voices()
    assert "sophie_en_zh" in result["voices"]


def test_ping_returns_ok():
    from seed_mcp.server import seed_ping
    with patch("seed_mcp.server.SeedClient") as MockClient:
        MockClient.return_value.ping.return_value = {
            "status": "ok", "version": "0.1.0", "provider": "fal",
            "credentials": {"fal_key": True},
        }
        result = seed_ping()
    assert result["status"] == "ok"
    assert result["provider"] == "fal"
