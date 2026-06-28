"""Focused tests for the fal provider's endpoints and status mapping."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from seed.providers.fal import FalProvider
from seed.types import AudioParams


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv("FAL_KEY", "k")
    return FalProvider()


def test_submit_url_and_auth_header(provider):
    with patch("seed.providers.fal.request_with_retry", return_value={"request_id": "r"}) as mock:
        provider.submit(AudioParams(prompt="hi"))
    url = mock.call_args.args[0]
    headers = mock.call_args.kwargs["headers"]
    assert url.endswith("/bytedance/seed-audio-1.0")
    assert headers["Authorization"] == "Key k"


def test_status_url(provider):
    with patch("seed.providers.fal.request_with_retry", return_value={"status": "IN_PROGRESS"}) as mock:
        provider.status("req-9")
    assert mock.call_args.args[0].endswith("/requests/req-9/status")


def test_status_maps_queue_states(provider):
    for raw, normalised in [("IN_QUEUE", "queued"), ("IN_PROGRESS", "running"), ("FAILED", "failed")]:
        with patch("seed.providers.fal.request_with_retry", return_value={"status": raw}):
            assert provider.status("r").status == normalised


def test_completed_triggers_result_fetch(provider):
    responses = [{"status": "COMPLETED"}, {"audio": {"url": "https://cdn/x.mp3"}}]
    with patch("seed.providers.fal.request_with_retry", side_effect=responses) as mock:
        result = provider.status("r")
    # two calls: status then result
    assert mock.call_count == 2
    assert result.audio_url == "https://cdn/x.mp3"
