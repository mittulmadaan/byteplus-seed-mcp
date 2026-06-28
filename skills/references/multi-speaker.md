# Multi-speaker & dialogue

Seed Audio can produce conversations, radio dramas, and multi-character scenes in a single
generation. The structure lives entirely in the `prompt`.

## Patterns

### Scripted dialogue
Label each line with the speaker. Keep turns short and natural.

```
prompt = """A two-person radio chat, warm and casual.
HOST: So — you drove all night to get here?
GUEST (laughing): Eleven hours. I'd do it again.
HOST: Tell me everything."""
```

### Radio drama / scene
Lead with the setting and mood, then the beats. Punctuation and stage directions cue pacing,
sound, and emotion.

```
prompt = "A short suspense radio drama in a late-night convenience store. Footsteps.
A door chime. CLERK (uneasy): 'We're… closing soon.' A long pause. Then a whisper."
```

### Distinct voices per character
Two routes:
- **Cloning** — give each character a reference clip and tag them `@Audio1`, `@Audio2`,
  `@Audio3` (see [reference-audio.md](reference-audio.md)). Best for consistent, specific voices.
- **Direction only** — describe each character's voice in prose ("a gravelly old sailor",
  "a bright young clerk") and let the model differentiate.

## Tips

- Keep a scene to a manageable length; generate long pieces in segments and stitch.
- Name characters consistently so turns stay coherent.
- Reuse the same reference clip across segments to keep a character's voice stable.
