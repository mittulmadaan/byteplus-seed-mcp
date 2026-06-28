# Voice & audio prompting

Seed Audio 1.0 reads the `prompt` both as the **text to speak** and as **direction** for how
to speak it. Shape the user's request before submitting.

## 1. Decide what `prompt` contains

- **Plain TTS** — the prompt is the literal text to be spoken. Keep punctuation natural; it
  drives pacing and intonation.
- **Directed delivery** — prefix or wrap the text with intent, e.g.
  *"Warm, unhurried narrator: 'Welcome back to the late show…'"*
- **Sound/scene** — describe the audio to generate, e.g.
  *"A short suspense radio drama set in a late-night convenience store."*

## 2. Control delivery

| Want | Use |
|---|---|
| Faster / slower | `speed` (0.5–2.0) — prefer this over writing "speak quickly" |
| Louder / softer | `volume` (0.5–2.0) |
| Higher / lower voice | `pitch` (semitones, −12…12) |
| Emotion / tone | Describe it in the prompt ("anxious whisper", "bright and upbeat") |
| Pauses / beats | Punctuation, line breaks, ellipses — and explicit stage directions |

## 3. Language

Most preset voices are multilingual (their id lists supported languages, e.g. `sophie_en_zh`
= English + Chinese). Write the `prompt` in the target language; the voice id must support it.

## 4. Keep it tight

- Put delivery direction at the **start**, then the spoken text.
- Don't over-specify — one or two adjectives of tone beat a paragraph.
- For long scripts, generate in segments and stitch, rather than one huge prompt.

See also: [voice-presets.md](voice-presets.md), [reference-audio.md](reference-audio.md),
[multi-speaker.md](multi-speaker.md).
