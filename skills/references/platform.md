# Platform, credentials & providers

Seed Audio 1.0 is reachable through **two interchangeable providers**, selected with
`SEED_PROVIDER`. The SDK hides the wire-format differences behind one interface, so the MCP
tools, CLI, and this skill behave the same either way.

| | `fal` (default) | `byteplus` |
|---|---|---|
| Backend | fal.ai `bytedance/seed-audio-1.0` | Volcengine Doubao `POST /api/v3/tts/create` |
| Model | hosted relay | native BytePlus API |
| Flow | **async** — submit → poll `seed_check_task` | **synchronous** — submit returns the audio in one call |
| Credential | `FAL_KEY` | `BYTEPLUS_SEED_API_KEY` (or legacy `BYTEPLUS_SEED_APP_ID` + `BYTEPLUS_SEED_ACCESS_KEY`) |
| Voice field | `voice` (fal preset ids) | `speaker` (Doubao TTS / clone voice ids) — **ids differ from fal's** |

> **Async vs sync matters.** With `fal`, `seed_audio_generate` returns `status: "queued"` and
> you poll `seed_check_task`. With `byteplus`, the same call returns `status: "completed"` with
> the `audio_url` already present — no polling. Both paths are handled automatically; just check
> whether the submit result already has `audio_url`.

## Credentials

First non-empty wins: explicit arg → env var → `~/.seed/credentials` → `.env`.

**fal** — `export FAL_KEY=<key>` (or `seed auth login`). Get a key at
<https://fal.ai/dashboard/keys>.

**byteplus** — set ONE of:
- `export BYTEPLUS_SEED_API_KEY=<key>` (new Volcengine Speech console — recommended), or
- `export BYTEPLUS_SEED_APP_ID=<id> BYTEPLUS_SEED_ACCESS_KEY=<key>` (legacy console).

Activate the service and collect keys at the Volcengine Speech console
(<https://console.volcengine.com/speech/>). Then `export SEED_PROVIDER=byteplus`.

Verify either provider with `seed ping` (CLI) or `seed_ping` (MCP) — it reports the active
provider and which credentials are present.

## Limits & cost

- Reference audio: ≤ 3 clips, ≤ 30s and ≤ 10 MB each (wav/mp3/pcm/ogg_opus).
- Reference image: 1 only, ≤ 10 MB (jpeg/png/webp). Cannot mix image + audio refs.
- BytePlus: `text_prompt` ≤ 2048 chars; output capped at 120s/request; returned `url` is
  temporary (~2h) — download promptly. Speed/volume map to BytePlus `speech_rate`/`loudness_rate`
  automatically; `pitch` maps to `pitch_rate` (−12…12).
- fal bills per request: <https://fal.ai/models/bytedance/seed-audio-1.0>. BytePlus bills per
  the Volcengine pricing for Seed Audio 1.0.
