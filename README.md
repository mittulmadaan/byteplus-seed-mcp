# BytePlus Seed Audio

Generate natural speech and audio with **BytePlus Seed Audio 1.0** — from Claude, the
terminal, or your own code. Three surfaces over one zero-dependency SDK:

| I want to… | Use |
|---|---|
| Talk to Claude / Claude Code | **MCP server** (`seed-mcp`) |
| Generate from the terminal | **CLI** (`seed`) |
| Claude Code skill | **Skill** (`skills/seed.md`) |
| Build my own integration | **SDK** (`seed-sdk`) |

> **Providers:** Seed Audio runs on **two interchangeable backends**, chosen with
> `SEED_PROVIDER`: **fal.ai** (`bytedance/seed-audio-1.0`, default, async) or **BytePlus /
> Volcengine Doubao** (`SEED_PROVIDER=byteplus`, the native `openspeech.bytedance.com` API,
> synchronous). The SDK hides the wire-format differences behind one interface — the MCP
> tools, CLI, and skill are identical either way. See
> [`seed/providers/`](packages/seed-sdk/seed/providers/).

## Prerequisites

- **Python 3.10+** and a local clone of this repo.
- Credentials for one provider:
  - **fal.ai** (default): a `FAL_KEY` — get one at <https://fal.ai/dashboard/keys>.
  - **BytePlus / Volcengine Doubao** (optional): `BYTEPLUS_SEED_API_KEY` (or the legacy
    `BYTEPLUS_SEED_APP_ID` + `BYTEPLUS_SEED_ACCESS_KEY`), then `SEED_PROVIDER=byteplus`.

## Install

```bash
git clone https://github.com/mittulmadaan/byteplus-seed-mcp
cd byteplus-seed-mcp

# Install the three packages
pip install ./packages/seed-sdk ./packages/seed-mcp ./packages/seed-cli

# Or, for development (uv workspace):
uv sync --all-packages --dev
```

> Not on PyPI yet — install from the repo. PyPI publishing kicks in on the first
> `sdk/v*` | `mcp/v*` | `cli/v*` release tag (see [Release](#release)).

---

## 🖥 MCP Server

Expose Seed Audio to Claude Desktop / Claude Code.

### Local (stdio)

After installing (above):

```bash
export FAL_KEY=<your-fal-key>
python -m seed_mcp                  # stdio transport (default)
```

Register it with `seed skill install` (below), or add it manually:

```json
{
  "mcpServers": {
    "seed": { "command": "python", "args": ["-m", "seed_mcp"] }
  }
}
```

### Hosted (Docker / SSE)

```bash
docker build -t byteplus-seed-mcp .
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=sse \
  -e FAL_KEY=<key> \
  -e MCP_AUTH_TOKEN=<strong-random-token> \
  byteplus-seed-mcp
# health: GET http://localhost:8000/health
```

A `render.yaml` is included for one-click Render deployment. Point your MCP client at
`https://<host>/mcp` (streamable HTTP) with a bearer token — credentials stay server-side,
clients authenticate with `MCP_AUTH_TOKEN` only:

```json
{
  "mcpServers": {
    "seed": {
      "type": "http",
      "url": "https://<host>/mcp",
      "headers": { "Authorization": "Bearer <MCP_AUTH_TOKEN>" }
    }
  }
}
```

### Tools

| Tool | Purpose |
|---|---|
| `seed_audio_generate` | Submit an audio job → returns `request_id` (or the `audio_url` directly on synchronous providers like BytePlus) |
| `seed_check_task` | Poll until `completed`; returns `audio_url` (fal/async) |
| `seed_list_voices` | List preset voice ids |
| `seed_list_models` | List Seed models + capabilities |
| `seed_ping` | Liveness, active provider, credential check |

---

## 💻 CLI

```bash
seed auth login                      # stores FAL_KEY in ~/.seed/credentials (installed above)

# Generate
seed generate \
  --prompt "A short suspense radio drama in a late-night convenience store." \
  --watch

# With a preset voice
seed voices                          # list presets
seed generate -p "Welcome back to the late show." -v sophie_en_zh --watch

# Voice cloning from reference audio
seed generate -p "In @Audio1's voice: 'Once upon a time…'" \
  --audio-ref https://cdn.example.com/narrator.mp3 --watch

# Track a job
seed status <request_id>
seed watch  <request_id>

# Skill management (Claude Desktop + Claude Code)
seed skill install
seed skill check
```

Run `seed --help` for the full command reference.

---

## 🧠 Claude Code Skill

`skills/seed.md` (+ `skills/references/`) teaches Claude Code how to use Seed Audio well —
prompting, voice presets, cloning, multi-speaker scenes, and safety.

```bash
seed skill install                   # copies the skill + registers the MCP server
# restart Claude Code, then just ask it to "generate a 20s upbeat intro voiceover"
```

---

## 📦 SDK

```python
from seed import SeedClient

client = SeedClient()                                  # provider from SEED_PROVIDER (default: fal)
result = client.submit_audio(
    "A short suspense radio drama in a late-night convenience store.",
    output_format="mp3",
)
# BytePlus is synchronous — `result` is already completed. fal is async, so poll.
import time
while not result.terminal:
    time.sleep(5)
    result = client.check_task(result.request_id)
print(result.audio_url)
```

`seed-sdk` has **zero runtime dependencies** (stdlib `urllib` only).

---

## Repo structure

```
byteplus-seed-mcp/
├── packages/
│   ├── seed-sdk/      # core: client, types, credentials, providers/{fal,byteplus}
│   ├── seed-mcp/      # FastMCP server (5 tools, stdio + SSE)
│   └── seed-cli/      # Typer + Rich CLI, skill installer
├── skills/            # seed.md + references/
├── Dockerfile         # SSE server image
├── render.yaml        # Render.com deployment
└── pyproject.toml     # uv workspace
```

## Credentials

Resolution order (first non-empty wins): explicit arg → env var → `~/.seed/credentials`
`[default]` → `.env`.

| Provider | Env var(s) |
|---|---|
| fal (default) | `FAL_KEY` |
| BytePlus (new console) | `BYTEPLUS_SEED_API_KEY` |
| BytePlus (legacy console) | `BYTEPLUS_SEED_APP_ID` + `BYTEPLUS_SEED_ACCESS_KEY` |

> Never commit credentials or bake them into images. Protect hosted SSE endpoints with
> `MCP_AUTH_TOKEN`.

## Release

Independent per-package PyPI publishes via tags:

```bash
git tag sdk/v0.1.0 && git push --tags   # → seed-sdk
git tag mcp/v0.1.0 && git push --tags   # → seed-mcp
git tag cli/v0.1.0 && git push --tags   # → seed-cli
```

## Providers

```bash
# fal (default, async)
export FAL_KEY=<key>            && export SEED_PROVIDER=fal

# BytePlus / Volcengine Doubao (synchronous — submit returns the audio directly)
export BYTEPLUS_SEED_API_KEY=<key>   # or BYTEPLUS_SEED_APP_ID + BYTEPLUS_SEED_ACCESS_KEY
export SEED_PROVIDER=byteplus
```

Voice ids differ between providers (fal presets vs Doubao `speaker` ids). `seed ping` shows
the active provider and which credentials are configured.

## Roadmap

- [x] Native BytePlus Seed Audio provider (`SEED_PROVIDER=byteplus`)
- [ ] Local-file upload helper (host local audio/images → public URL)
- [ ] Additional Seed models as they ship

## Support

- Repo: <https://github.com/mittulmadaan/byteplus-seed-mcp>
- Seed Audio on fal: <https://fal.ai/models/bytedance/seed-audio-1.0>
- fal queue API: <https://docs.fal.ai/model-endpoints/queue>
- Volcano Engine (BytePlus) Audio Generation API: <https://www.volcengine.com/docs/6561/2550782>
