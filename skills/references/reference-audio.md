# Reference audio & image inputs

Seed Audio can **clone a voice** from reference audio, or take a **reference image** as a
conditioning input. These two are **mutually exclusive** — pass `audio_urls` OR `image_url`,
never both.

## Voice cloning with `audio_urls`

- Pass **up to 3** public reference audio URLs in `audio_urls`.
- Each clip: **≤ 30 seconds**, **≤ 10 MB**, publicly fetchable (no localhost, no expiring
  signed URLs).
- In the `prompt`, refer to each clip **by order**: the first URL is `@Audio1`, the second
  `@Audio2`, the third `@Audio3`.

### Example

```
audio_urls = [
  "https://cdn.example.com/narrator.mp3",   # @Audio1
  "https://cdn.example.com/child.mp3",       # @Audio2
]
prompt = "In @Audio1's calm voice: 'Once upon a time…'  Then @Audio2 giggles: 'Again!'"
```

`@Audio1` clones the narrator's timbre; `@Audio2` clones the child's. Combine with a preset
`voice` only when you want a preset for the un-tagged narration.

## Reference image with `image_url`

- One public image URL (jpeg / png / webp, ≤ 10 MB).
- Use when the user wants audio conditioned on an image (e.g. a character portrait driving
  voice character). Cannot be combined with `audio_urls`.

## Public URL requirement (today)

The fal provider fetches references over the network, so **local file paths do not work yet**.
If the user only has a local file:
1. Ask them to host it on a public bucket / CDN and pass the URL, or
2. Note that a local-upload helper is planned for a future release.

See also: [voice-prompting.md](voice-prompting.md), [safety.md](safety.md).
