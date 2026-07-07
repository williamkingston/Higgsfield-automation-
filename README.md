# Higgsfield Automation

Automates video generation workflows on the [Higgsfield AI](https://higgsfield.ai)
platform — programmatic generation, batch pipelines, and orchestration of
rendering jobs.

Generation runs through the **Higgsfield MCP connector** (verified live against
the real model catalog). This repo is the pure-Python layer that builds and
validates connector requests, preflights cost, and tracks jobs — the connector
call itself is supplied by the agent/host (see Architecture).

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt        # add -r requirements-dev.txt for tests
```

No API keys are required: the Higgsfield connector is authorized per-session via
OAuth in your agent client, not via secrets in `.env`.

## Usage

The client is **transport-injected** — you pass an `invoker(tool, args)` that
performs the actual connector call. In an agent session that forwards to the
Higgsfield MCP tools; in tests it's a fake.

### Preflight cost (free — no job created)

```python
from src import HiggsfieldConnectorClient

client = HiggsfieldConnectorClient(invoker)   # invoker bridges the MCP connector
credits = client.preflight_cost("seedance_2_0_mini", "a calm ocean", duration=5)
```

### Submit + track (restart-safe)

```python
job_ids = client.submit("seedance_2_0", "a neon city at night", duration=5)
# ... persist job_ids somewhere durable ...
result = client.wait_for_job(job_ids[0])
if result.succeeded:
    client.download(result.output_url, "output/city.mp4")
```

Valid model ids live in [`src/models.py`](src/models.py) (e.g. `seedance_2_0`,
`seedance_2_0_mini`, `kling3_0`, `kling3_0_turbo`, `veo3_1`). Passing an unknown
id raises with suggestions.

### Batch

Describe jobs in a JSON file (see [`jobs.example.json`](jobs.example.json)).
`scripts/run_batch.py` validates them against the catalog and emits the exact
`generate_video` payloads to submit through the connector:

```bash
python scripts/run_batch.py jobs.example.json
```

`src/batch.py`'s `BatchRunner` persists each job id to a state file; re-running
with the same state file **resumes** — completed jobs are skipped and in-flight
jobs are recovered by id rather than re-submitted.

## Architecture

- **`src/models.py`** — verified model registry (real ids, durations, aspect
  ratios) sourced from the connector's live catalog.
- **`src/client.py`** — `HiggsfieldConnectorClient`: builds/validates
  `generate_video` requests, preflights cost, submits, polls, downloads. The
  connector call is injected (`invoker`), so it's fully testable.
- **`src/batch.py`** — resumable batch runner over a JSON state file.
- **`scripts/run_batch.py`** — validates a jobs file and emits connector payloads.
- **`.agents/skills/`** — vendored agent skills (impeccable, taste-skills,
  OpenMontage AI-video skills) for AI-assisted development.

See [`docs/openmontage-integration.md`](docs/openmontage-integration.md) for the
background, including why the earlier REST approach was replaced.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests use a fake invoker — they never hit the network, spend credits, or need
credentials.
