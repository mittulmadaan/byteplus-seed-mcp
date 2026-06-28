# BytePlus Seed Audio

Generate natural speech and audio with **BytePlus Seed Audio 1.0** — from Claude, the
terminal, or your own code. Three surfaces over one zero-dependency SDK:

| I want to… | Use |
|---|---|
| Talk to Claude / Claude Code | **MCP server** (`seed-mcp`) |
| Generate from the terminal | **CLI** (`seed`) |
| Claude Code skill | **Skill** (`skills/seed.md`) |
| Build my own integration | **SDK** (`seed-sdk`) |

> **Provider:** Seed Audio runs on **fal.ai** (`bytedance/seed-audio-1.0`) today. The SDK
> hides this behind a provider abstraction, so when BytePlus releases its native Seed Audio
> API you flip `SEED_PROVIDER=byteplus` (and add `BYTEPLUS_SEED_API_KEY`) — nothing else
> changes. See [`seed/providers/`](packages/seed-sdk/seed/providers/).

## Prerequisites

- Python 3.10+
- A **fal.ai API key** → set `FAL_KEY` (get one at <https://fal.ai/dashboard/keys>).

## Install (workspace, for development)

```bash
uv sync --all-packages --dev      # installs seed-sdk, seed-mcp, seed-cli
```

---

## 🖥 MCP Server

Expose Seed Audio to Claude Desktop / Claude Code.

```bash
pip install seed-mcp                # or: uv pip install ./packages/seed-mcp
export FAL_KEY=<your-fal-key>
python -m seed_mcp                  # stdio transport (default)
```

Register it (or use the CLI installer, below). Claude config:

```json
{
  "mcpServers": {
    "seed": { "command": "python", "args": ["-m", "seed_mcp"] }
  }
}
```

### Tools

| Tool | Purpose |
|---|---|
| `seed_audio_generate` | Submit an audio job → returns `request_id` |
| `seed_check_task` | Poll until `completed`; returns `audio_url` |
| `seed_list_voices` | List preset voice ids |
| `seed_list_models` | List Seed models + capabilities |
| `seed_ping` | Liveness, provider, credential check |

### Hosted / Docker

```bash
docker build -t byteplus-seed-mcp .
docker run -e FAL_KEY=<key> -e MCP_TRANSPORT=sse -p 8000:8000 byteplus-seed-mcp
# health: GET http://localhost:8000/health
```

---

## 💻 CLI

```bash
pip install seed-cli                 # or: pip install 'seed-cli[mcp]'
seed auth login                      # stores FAL_KEY in ~/.seed/credentials

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
task = client.submit_audio(
    "A short suspense radio drama in a late-night convenience store.",
    output_format="mp3",
)
# poll until done
import time
while not (result := client.check_task(task.request_id)).terminal:
    time.sleep(5)
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

Resolution order (first non-empty wins): explicit arg → `FAL_KEY` env →
`~/.seed/credentials` `[default]` → `.env`.

## Release

Independent per-package PyPI publishes via tags:

```bash
git tag sdk/v0.1.0 && git push --tags   # → seed-sdk
git tag mcp/v0.1.0 && git push --tags   # → seed-mcp
git tag cli/v0.1.0 && git push --tags   # → seed-cli
```

## Roadmap

- [ ] Native BytePlus Seed Audio provider (`SEED_PROVIDER=byteplus`)
- [ ] Local-file upload helper (host local audio/images → public URL)
- [ ] Additional Seed models as they ship

## Support

- Seed Audio model: <https://fal.ai/models/bytedance/seed-audio-1.0>
- fal queue API: <https://docs.fal.ai/model-endpoints/queue>
