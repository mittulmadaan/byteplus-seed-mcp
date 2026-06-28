# Platform, credentials & provider

## Provider: fal.ai today, BytePlus later

Seed Audio 1.0 is served through **fal.ai** (`bytedance/seed-audio-1.0`). The SDK wraps this
behind a provider abstraction, so when BytePlus ships its native Seed Audio API the backend
swaps with no change to tools, CLI, or this skill.

- `SEED_PROVIDER=fal` (default) — uses fal.ai. Requires `FAL_KEY`.
- `SEED_PROVIDER=byteplus` — reserved; raises "not yet available" until the native API ships
  and `BYTEPLUS_SEED_API_KEY` is configured.

## Credentials

Set the fal.ai API key via any of (first wins):

1. `export FAL_KEY=<key>`
2. `seed auth login` → stores it in `~/.seed/credentials` (chmod 600)
3. `~/.seed/credentials`:
   ```ini
   [default]
   fal_key = <key>
   ```
4. A `.env` file in the working directory (if `python-dotenv` is installed).

Get a key at <https://fal.ai/dashboard/keys>. Verify with `seed ping` (CLI) or `seed_ping` (MCP).

## Limits & cost

- Reference audio: ≤ 3 clips, ≤ 30s and ≤ 10 MB each.
- Reference image: ≤ 10 MB.
- Generation is **asynchronous** — submit returns a `request_id`; poll every 5–10s.
- fal bills per request; check current pricing on the model page:
  <https://fal.ai/models/bytedance/seed-audio-1.0>.
