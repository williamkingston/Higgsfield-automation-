# OpenMontage ↔ Higgsfield-automation integration

How [OpenMontage](https://github.com/calesthio/OpenMontage) — an open-source,
agent-driven video production system — relates to this repository, and how its
pipeline could plug in.

## TL;DR

The client was first ported from OpenMontage's REST tool
(`tools/video/higgsfield_video.py`), then — after live validation — **pivoted to
the Higgsfield MCP connector**. `src/client.py` now builds and validates
`generate_video` requests against the real model catalog (`src/models.py`) and
delegates the actual call to an injected transport.

## Update (2026-06-16): validated, then pivoted to the connector

Live validation against the real Higgsfield account (605.5 credits, "ultimate")
surfaced a decisive problem with the ported REST approach:

- The REST surface (`platform.higgsfield.ai/v1`) is **blocked by this
  environment's network policy** (403 `host_not_allowed`) and no REST creds exist.
- The model ids OpenMontage hard-coded **do not match** the real catalog:
  `seedance_2.0`→`seedance_2_0`, `kling_3.0`→`kling3_0`, `veo_3.1`→`veo3_1`, and
  `sora_2` / `soul_cinema` **don't exist at all**.

So the client was rebuilt on the **MCP connector**, which is authorized and
proven live. Verified facts baked into the code:

- Request envelope is `{"params": {"model": ..., "prompt": ..., ...}}`.
- Real model ids come from the connector's `models_explore` catalog
  (`src/models.py`).
- `generate_video` with `get_cost: true` preflights credits **without** creating
  a job; response is `{"cost": {"credits": N}}`. A 5s `seedance_2_0_mini` clip = 12.5 credits.

Because an MCP connector can't be called from plain Python, `src/client.py` is
**transport-injected**: the agent (or host bridge) supplies the `invoker`; the
Python owns request-building, validation, cost preflight, job tracking, and
download — all unit-tested with a fake invoker.

### Original port (historical)

OpenMontage's `higgsfield_video` tool talks to a Higgsfield Cloud REST API and
was the starting point; the notes below describe that surface.

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
