---
name: seed
description: Generate speech and audio with BytePlus Seed Audio 1.0 — text-to-speech, voice presets, voice cloning from reference audio, multi-speaker drama, and task tracking. Runs on fal.ai today.
version: 0.1.0
---

# Seed Audio Generation

Use this skill to generate speech and audio with **BytePlus Seed Audio 1.0** directly from
Claude Code. Seed Audio turns text (plus optional reference audio or an image) into natural,
high-quality speech and sound.

> **Provider note:** Seed Audio currently runs through **fal.ai**
> (`bytedance/seed-audio-1.0`). When BytePlus releases its native API, the backend swaps with
> no change to these tools — set `SEED_PROVIDER=byteplus`. See
> [`references/platform.md`](references/platform.md).

---

## 🚦 Pre-flight

1. **Craft the prompt first.** Before calling `seed_audio_generate`, shape the user's request
   into an effective audio prompt — see [`references/voice-prompting.md`](references/voice-prompting.md).
2. **Pick a voice path.** Either a **preset voice** (`seed_list_voices`) or **voice cloning**
   from reference audio — see [`references/voice-presets.md`](references/voice-presets.md) and
   [`references/reference-audio.md`](references/reference-audio.md).
3. **Confirm before submitting** when the request is ambiguous (which voice? which language?
   one speaker or several?).

---

## Core rules

1. **Async only.** `seed_audio_generate` returns a `request_id` immediately. Poll
   `seed_check_task(request_id)` every **5–10 seconds** until `status == "completed"`, which
   carries `audio_url`. Never assume the audio is ready on submit.
2. **One voice path at a time.** `voice` (preset) and `audio_urls` (cloning) can be combined,
   but `audio_urls` and `image_url` are **mutually exclusive** — pass one or the other.
3. **Reference inputs must be PUBLIC URLs.** `audio_urls` (≤3, ≤30s & ≤10MB each) and
   `image_url` (≤10MB) must be URLs reachable by fal. Local file paths are **not supported
   yet** — ask the user for a public URL or to host the file.
4. **Reference clones by order.** In the prompt, refer to reference audio as `@Audio1`,
   `@Audio2`, `@Audio3`, matching the order of `audio_urls`. See
   [`references/reference-audio.md`](references/reference-audio.md).
5. **Multi-speaker / dialogue** (radio drama, conversations): see
   [`references/multi-speaker.md`](references/multi-speaker.md).
6. **Defaults:** `output_format=mp3`, `sample_rate=24000`, `speed=1.0`, `volume=1.0`. Only
   change these when the user asks (e.g. `wav` for editing, `48000` for high fidelity).
7. **Voice cloning needs consent.** Only clone voices the user is authorised to use. See
   [`references/safety.md`](references/safety.md).
8. **Hand back the `audio_url`** when complete. The URL is the deliverable — share it, or
   download it if the user wants a local file.

---

## MCP tools

| Tool | Purpose |
|---|---|
| `seed_audio_generate` | Submit an audio job (prompt + voice/audio_urls/image_url + format/rate/speed/volume/pitch). Returns `request_id`. |
| `seed_check_task` | Poll a job; returns `audio_url` when `status == "completed"`. |
| `seed_list_voices` | List the preset voice ids. |
| `seed_list_models` | List Seed models + capabilities. |
| `seed_ping` | Check liveness, active provider, and credentials. |

### Parameters for `seed_audio_generate`

- `prompt` (required) — text to speak, or a description of the audio. Reference clones as `@Audio1…`.
- `voice` — preset voice id (omit when cloning only).
- `audio_urls` — up to 3 public reference audio URLs (voice cloning).
- `image_url` — one public reference image URL (mutually exclusive with `audio_urls`).
- `output_format` — `mp3` | `wav` | `pcm` | `ogg_opus` (default `mp3`).
- `sample_rate` — `8000` | `16000` | `24000` | `32000` | `44100` | `48000` (default `24000`).
- `speed` — `0.5`–`2.0` (default `1.0`). `volume` — `0.5`–`2.0` (default `1.0`).
- `pitch` — semitones, `-12`…`12` (`0` = normal).

---

## Typical flow

1. Clarify intent (voice, language, single vs multi-speaker).
2. (Optional) `seed_list_voices` to pick a preset.
3. Craft the prompt ([`references/voice-prompting.md`](references/voice-prompting.md)).
4. `seed_audio_generate(...)` → get `request_id`.
5. Poll `seed_check_task(request_id)` every 5–10s until `completed`.
6. Return the `audio_url`.

## Troubleshooting

- **`FAL_KEY is not configured`** → run `seed auth login` or `export FAL_KEY=...`. See
  [`references/platform.md`](references/platform.md).
- **`audio_urls and image_url are mutually exclusive`** → pass only one.
- **`Too many audio_urls`** → max 3 reference clips.
- **Reference URL rejected / 4xx** → the URL must be publicly fetchable (not localhost, not a
  signed URL that expires); re-host on a public bucket.
- **`BytePlus Seed Audio API is not yet available`** → `SEED_PROVIDER` is set to `byteplus`;
  unset it (or set `fal`) until the native API ships.
