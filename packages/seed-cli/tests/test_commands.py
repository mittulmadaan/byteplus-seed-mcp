"""CLI command tests using Typer's test runner."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from seed.types import TaskResult
from seed_cli.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("FAL_KEY", "test-fal-key")


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

def test_generate_prints_request_id():
    mock_result = TaskResult(request_id="req-abc", status="queued", provider="fal")
    with patch("seed_cli.commands.generate.SeedClient") as MockClient:
        MockClient.return_value.submit_audio.return_value = mock_result
        result = runner.invoke(app, ["generate", "--prompt", "Hello world"])
    assert result.exit_code == 0
    assert "req-abc" in result.output


def test_generate_missing_prompt_fails():
    result = runner.invoke(app, ["generate"])
    assert result.exit_code != 0


def test_generate_forwards_voice_and_audio_ref():
    mock_result = TaskResult(request_id="req-1", status="queued", provider="fal")
    with patch("seed_cli.commands.generate.SeedClient") as MockClient:
        MockClient.return_value.submit_audio.return_value = mock_result
        result = runner.invoke(app, [
            "generate", "--prompt", "She says @Audio1",
            "--voice", "sophie_en_zh",
            "--audio-ref", "https://example.com/voice.mp3",
        ])
    assert result.exit_code == 0
    kwargs = MockClient.return_value.submit_audio.call_args.kwargs
    assert kwargs["voice"] == "sophie_en_zh"
    assert kwargs["audio_urls"] == ["https://example.com/voice.mp3"]


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

def test_status_completed_shows_url():
    mock_result = TaskResult(
        request_id="req-123", status="completed", audio_url="https://cdn.fal.ai/out.mp3",
    )
    with patch("seed_cli.commands.tasks.SeedClient") as MockClient:
        MockClient.return_value.check_task.return_value = mock_result
        result = runner.invoke(app, ["status", "req-123"])
    assert result.exit_code == 0
    assert "completed" in result.output
    assert "https://cdn.fal.ai/out.mp3" in result.output


def test_status_failed_exits_nonzero():
    mock_result = TaskResult(request_id="req-bad", status="failed", error={"msg": "boom"})
    with patch("seed_cli.commands.tasks.SeedClient") as MockClient:
        MockClient.return_value.check_task.return_value = mock_result
        result = runner.invoke(app, ["status", "req-bad"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# voices / models
# ---------------------------------------------------------------------------

def test_voices_lists_presets():
    with patch("seed_cli.commands.voices.SeedClient") as MockClient:
        MockClient.return_value.list_voices.return_value = {
            "voices": ["sophie_en_zh", "felix_zh"], "count": 2,
        }
        result = runner.invoke(app, ["voices"])
    assert result.exit_code == 0
    assert "sophie_en_zh" in result.output


def test_models_lists_seed_audio():
    with patch("seed_cli.commands.models.SeedClient") as MockClient:
        MockClient.return_value.list_models.return_value = {
            "default_model": "seed-audio-1.0",
            "provider": "fal",
            "models": [{
                "model_id": "seed-audio-1.0", "label": "Seed Audio 1.0",
                "provider": "fal", "output_formats": ["mp3"], "sample_rates": [24000],
            }],
        }
        result = runner.invoke(app, ["models"])
    assert result.exit_code == 0
    assert "seed-audio-1.0" in result.output


# ---------------------------------------------------------------------------
# auth check / ping
# ---------------------------------------------------------------------------

def test_auth_check_configured(tmp_path, monkeypatch):
    monkeypatch.setattr("seed.credentials.CREDENTIALS_PATH", tmp_path / "credentials")
    result = runner.invoke(app, ["auth", "check"])
    assert result.exit_code == 0
    assert "configured" in result.output


def test_auth_check_missing_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.delenv("FAL_KEY", raising=False)
    monkeypatch.setattr("seed.credentials.CREDENTIALS_PATH", tmp_path / "credentials")
    result = runner.invoke(app, ["auth", "check"])
    assert result.exit_code != 0


def test_ping_ok(tmp_path, monkeypatch):
    monkeypatch.setattr("seed.credentials.CREDENTIALS_PATH", tmp_path / "credentials")
    result = runner.invoke(app, ["ping"])
    assert result.exit_code == 0
    assert "Ready" in result.output
