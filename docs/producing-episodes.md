# Producing Episodes — the durable workflow

This project can render an episode two ways. For anything beyond a quick test,
prefer the **headless pipeline** — it avoids the interactive-approval, connector-
churn, and chat-babysitting issues that make ad-hoc generation fragile.

## Headless pipeline (recommended for real episodes)

One command submits every scene, polls to completion, downloads the clips, and
assembles them into a single `episode.mp4`. No per-tool approval prompts, no
manual polling.

```bash
# 1. Set your key once (or put it in .env)
export HIGGSFIELD_API_KEY=sk-...

# 2. Render a single episode, or the whole series
python scripts/generate_episode.py series/mythrealm.yaml --episode 1
python scripts/generate_episode.py series/mythrealm.yaml --all
```

Output lands in `output/<series>/ep01/`:
- `scene-XX.mp4` — one clip per scene
- `episode.mp4` — the assembled episode
- `jobs.json` — per-scene job records (used for **resume**)
- `manifest.json` — episode summary

**Resume:** re-running the same command skips scenes already completed (tracked in
`jobs.json`), so an interrupted render picks up where it left off — no wasted credits.

**Consistency:** put a canonical image path in each scene's `image_reference` (see
`series/mythrealm.yaml`); the backend feeds it as an identity reference so
characters/creatures stay on-model across shots.

## Why this avoids the common failure modes

| Past issue | Why it happened | How the headless path fixes it |
|---|---|---|
| "MCP tool requires approval" walls | Interactive connector tools default to "ask" | Direct API calls — no per-call approval |
| Connectors disconnecting mid-render | ~40 chat connectors churning | The pipeline uses one HTTP client, not chat MCP |
| Can't stitch (CDN blocked) | Sandbox network policy | Clips download via the API client + assemble locally |
| `ModuleNotFoundError: httpx` | Fresh sessions reset the env | `SessionStart` hook runs `scripts/setup_env.sh` |
| ffmpeg missing for assembly | No system ffmpeg | `assemble.py` falls back to bundled `imageio-ffmpeg` |

## Environment hardening (already wired)

- **`.claude/settings.json`** runs `scripts/setup_env.sh` on every session start,
  installing runtime deps + a bundled ffmpeg. Safe to run by hand too.
- **`scripts/setup_env.sh`** is idempotent — instant on warm sessions.

## Operational checklist for a smooth run

1. **Credits** — a ~50s teaser ≈ 200 credits; an 11–22 min episode ≈ 4k–8k.
   Top up to your target and enable **auto-refill** so a render never dies halfway.
2. **Connectors** — for focused work, keep only what you need enabled; fewer
   connectors means less reconnect churn.
3. **API key** — the headless path needs `HIGGSFIELD_API_KEY`; keep it in `.env`
   (already git-ignored), never commit it.
