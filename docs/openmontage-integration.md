# OpenMontage ↔ Higgsfield-automation integration

How [OpenMontage](https://github.com/calesthio/OpenMontage) — an open-source,
agent-driven video production system — relates to this repository, and how its
pipeline could plug in.

## TL;DR

OpenMontage already ships a working **Higgsfield Cloud API** client
(`tools/video/higgsfield_video.py`). This repo's first concrete step
(`src/client.py`) is a trimmed, standalone port of it that matches the
conventions in `CLAUDE.md`: a single client module, async submit → poll →
download, and exponential backoff on `429`.

## The linchpin: OpenMontage is already a Higgsfield consumer

OpenMontage's `higgsfield_video` tool talks to Higgsfield Cloud directly:

- **Auth:** `HIGGSFIELD_API_KEY` + `HIGGSFIELD_API_SECRET` (or combined
  `HIGGSFIELD_KEY="key:secret"`), sent as `Authorization: Bearer <key>` +
  `X-API-Secret: <secret>`. Keys from <https://cloud.higgsfield.ai/api-keys>.
- **Flow:** `POST /v1/generations` → poll `status_url` every ~5s → download
  `output_url`.
- **Models:** `seedance_2.0` (default), `seedance_2.0_fast`, `kling_3.0`,
  `veo_3.1`, `sora_2`, `wan_2.5`, `soul_cinema` — one key, multi-model routing,
  Soul ID character consistency, native audio.
- **Built in:** per-model/duration cost estimates, retry on `rate_limit` /
  `timeout`, idempotency keys.

## How OpenMontage is architected

Instruction-driven / agent-first: the AI agent orchestrates; Python is only
tools and persistence. Three knowledge layers:

| Layer | What | Where | Status in this repo |
|---|---|---|---|
| 3 | Generic API/tech knowledge | `.agents/skills/` | ✅ installed (the 81 vendored skills) |
| 2 | Project conventions ("when to use what") | `skills/` | not imported |
| 1 | Runtime tools (`BaseTool` + registry) | `tools/`, `lib/` | partially ported → `src/client.py` |

Pipeline state machine: `idea → script → scene_plan → assets → edit → compose →
publish`, driven by declarative YAML manifests, with a cost tracker
(`estimate → reserve → reconcile`), checkpoint/approval gates, and JSON-schema'd
artifacts (`brief`, `script`, `scene_plan`, `asset_manifest`, `edit_decisions`,
`render_report`).

## Alignment with this repo's `CLAUDE.md`

| `CLAUDE.md` requirement | OpenMontage equivalent | Here |
|---|---|---|
| Single client module for all Higgsfield calls | `tools/video/higgsfield_video.py` | `src/client.py` |
| Async job polling until `completed`/`failed` | submit → poll → download loop | `wait_for_generation()` |
| Backoff on `429` | `RetryPolicy(retryable_errors=[...])` | `_request()` exponential backoff + `Retry-After` |
| Persist job IDs across restarts | `lib/checkpoint.py` + `pipeline/` | `submit_generation()` returns the id to persist |
| Never log keys | env-var credential loading | logs request ids only, never secrets |

## Integration paths (least → most invasive)

1. **Vendor just the client (done).** `src/client.py` is a standalone
   `HiggsfieldClient` with async polling + `429` backoff. Smallest,
   highest-value step.
2. **Adopt the artifact + pipeline model.** Borrow the `idea → … → publish`
   state machine and JSON artifact schemas to drive batch Higgsfield jobs, with
   checkpointed job ids for restart recovery.
3. **Run OpenMontage as the engine, this repo as the orchestrator.** Keep
   OpenMontage whole; this repo schedules/queues jobs, calls its tools, and
   handles downstream delivery (CDN / social).

## Open question to reconcile

`CLAUDE.md` originally assumed `https://api.higgsfield.ai` with plain bearer
auth. OpenMontage (and therefore `src/client.py`) targets
`https://platform.higgsfield.ai/v1` with a **key + secret** pair. The base URL
is configurable via `HIGGSFIELD_API_BASE`; confirm which surface your account
uses before going to production, since it determines the auth headers and
endpoint.

## Usage

```python
from src import HiggsfieldClient

client = HiggsfieldClient.from_env()

# Fire-and-await (simple cases):
result = client.generate_video(
    "a neon city skyline at night, cinematic",
    model="seedance_2.0",
    duration=5,
    output_path="output/city.mp4",
)

# Batch / restart-safe (persist the id, await later):
gen_id = client.submit_generation("a forest spirit, ghibli style")
# ... store gen_id ...
result = client.wait_for_generation(gen_id)
if result.succeeded:
    client.download(result.output_url, "output/spirit.mp4")
```
