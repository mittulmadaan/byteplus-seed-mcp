# Preset voices

Call `seed_list_voices` (MCP) or `seed voices` (CLI) for the live list. A voice id encodes the
languages it supports — e.g. `sophie_en_zh` speaks English and Chinese, `vivi_mixed_en_zh_ja_es_id`
is multilingual across English/Chinese/Japanese/Spanish/Indonesian.

## Current presets

| Voice id | Languages |
|---|---|
| `vivi_mixed_en_zh_ja_es_id` | en, zh, ja, es, id (mixed) |
| `mindy_en_es_id_pt_zh` | en, es, id, pt, zh |
| `kian_en_zh` | en, zh |
| `cedric_en_zh` | en, zh |
| `sophie_en_zh` | en, zh |
| `jean_en_zh` | en, zh |
| `magnus_en_zh` | en, zh |
| `mabel_en_zh` | en, zh |
| `nadia_en_zh` | en, zh |
| `opal_en_zh` | en, zh |
| `pearl_en_zh` | en, zh |
| `quentin_en_zh` | en, zh |
| `corinne_mixed_en_zh` | en, zh (mixed) |
| `esther_mixed_en_zh` | en, zh (mixed) |
| `lyla_mixed_en_zh` | en, zh (mixed) |
| `tracy_es_zh` | es, zh |
| `sandy_es_mixed_en_zh` | es, en, zh (mixed) |
| `felix_zh` | zh |
| `celeste_zh` | zh |
| `monkey_king_zh` | zh (character voice) |

## Choosing

- Match the voice's languages to the prompt's language.
- "mixed" voices handle code-switching within one utterance.
- Character voices (e.g. `monkey_king_zh`) carry a strong persona — use intentionally.
- No preset fits? Clone a voice from reference audio — see [reference-audio.md](reference-audio.md).

> The preset list can change on fal. Always trust `seed_list_voices` over this table.
