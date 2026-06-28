"""fal.ai provider for Seed Audio 1.0 — queue submit + poll.

Queue REST flow (https://docs.fal.ai/model-endpoints/queue):
  submit  POST {base}/{model}                          -> {request_id, ...}
  status  GET  {base}/{model}/requests/{id}/status      -> {status, ...}
  result  GET  {base}/{model}/requests/{id}             -> {audio: {...}}
Auth header: `Authorization: Key <FAL_KEY>`.
"""
from __future__ import annotations

from ..config import (
    FAL_MODEL,
    FAL_QUEUE_BASE,
    POLL_TIMEOUT,
    SUBMIT_TIMEOUT,
)
from ..credentials import credentials_configured, load_fal_key
from ..http import extract_nested, request_with_retry
from ..types import AudioParams, TaskResult
from .base import AudioProvider

# fal queue status -> SDK normalised status
_STATUS_MAP = {
    "IN_QUEUE": "queued",
    "IN_PROGRESS": "running",
    "COMPLETED": "completed",
    "ERROR": "failed",
    "FAILED": "failed",
}


class FalProvider(AudioProvider):
    name = "fal"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str = FAL_MODEL,
        profile: str = "default",
    ) -> None:
        self._explicit_key = api_key
        self._profile = profile
        self.model = model

    # -- auth -------------------------------------------------------------
    def _headers(self) -> dict[str, str]:
        key = load_fal_key(self._explicit_key, profile=self._profile)
        return {
            "Authorization": f"Key {key}",
            "Content-Type": "application/json",
        }

    def configured(self) -> bool:
        return credentials_configured(profile=self._profile)["fal_key"]

    # -- endpoints --------------------------------------------------------
    def _submit_url(self) -> str:
        return f"{FAL_QUEUE_BASE}/{self.model}"

    def _status_url(self, request_id: str) -> str:
        return f"{FAL_QUEUE_BASE}/{self.model}/requests/{request_id}/status"

    def _result_url(self, request_id: str) -> str:
        return f"{FAL_QUEUE_BASE}/{self.model}/requests/{request_id}"

    # -- API --------------------------------------------------------------
    def submit(self, params: AudioParams) -> TaskResult:
        params.validate()
        resp = request_with_retry(
            self._submit_url(),
            method="POST",
            headers=self._headers(),
            payload=params.to_input(),
            timeout=SUBMIT_TIMEOUT,
        )
        request_id = str(resp.get("request_id") or resp.get("requestId") or "")
        status = _STATUS_MAP.get(str(resp.get("status", "")).upper(), "queued")
        return TaskResult(
            request_id=request_id,
            status=status,
            provider=self.name,
            raw=resp,
        )

    def status(self, request_id: str) -> TaskResult:
        resp = request_with_retry(
            self._status_url(request_id),
            method="GET",
            headers=self._headers(),
            timeout=POLL_TIMEOUT,
        )
        status = _STATUS_MAP.get(str(resp.get("status", "")).upper(), "running")

        if status != "completed":
            error = None
            if status == "failed":
                error = {"detail": resp.get("error") or resp}
            return TaskResult(
                request_id=request_id,
                status=status,
                error=error,
                provider=self.name,
                raw=resp,
            )

        # Completed — fetch the actual result payload for the audio URL.
        result = request_with_retry(
            self._result_url(request_id),
            method="GET",
            headers=self._headers(),
            timeout=POLL_TIMEOUT,
        )
        audio = result.get("audio") if isinstance(result.get("audio"), dict) else None
        audio_url = extract_nested(result, "audio", "url")
        return TaskResult(
            request_id=request_id,
            status="completed",
            audio_url=audio_url,
            audio=audio,
            provider=self.name,
            raw=result,
        )
