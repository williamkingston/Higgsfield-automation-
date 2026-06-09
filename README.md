# Higgsfield Automation

Automates video generation workflows on the [Higgsfield AI](https://higgsfield.ai)
platform — programmatic generation, batch pipelines, and orchestration of
rendering jobs.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt        # add -r requirements-dev.txt for tests

cp .env.example .env                   # then fill in your credentials
```

## Configure

Get a key + secret from <https://cloud.higgsfield.ai/api-keys> and set them in
`.env`:

| Variable | Description |
|---|---|
| `HIGGSFIELD_API_KEY` | Higgsfield Cloud API key |
| `HIGGSFIELD_API_SECRET` | Higgsfield Cloud API secret |
| `HIGGSFIELD_KEY` | Optional combined `key:secret` (alternative to the two above) |
| `HIGGSFIELD_API_BASE` | API base URL (default `https://platform.higgsfield.ai/v1`) |

## Usage

### Single generation

```python
from src import HiggsfieldClient

client = HiggsfieldClient.from_env()

result = client.generate_video(
    "a neon city skyline at night, cinematic",
    model="seedance_2.0",
    duration=5,
    output_path="output/city.mp4",
)
print(result.status, result.output_url)
```

### Restart-safe (submit now, await later)

```python
gen_id = client.submit_generation("a forest spirit, ghibli style")
# ... persist gen_id somewhere durable ...
result = client.wait_for_generation(gen_id)
if result.succeeded:
    client.download(result.output_url, "output/spirit.mp4")
```

### Batch

Describe jobs in a JSON file (see [`jobs.example.json`](jobs.example.json)), then:

```bash
python scripts/run_batch.py jobs.example.json --state pipeline/batch_state.json
```

The runner persists each job's generation id to the state file. Re-running with
the same state file **resumes** — completed jobs are skipped and in-flight jobs
are recovered by id rather than re-submitted.

## Architecture

- **`src/client.py`** — the single Higgsfield API client. All API calls go
  through it (async submit → poll → download, exponential backoff on `429`,
  request-id logging, never logs secrets).
- **`src/batch.py`** — resumable batch runner over a JSON state file.
- **`scripts/run_batch.py`** — CLI entry point for batches.
- **`.agents/skills/`** — vendored agent skills (impeccable, taste-skills,
  OpenMontage AI-video skills) for AI-assisted development.

See [`docs/openmontage-integration.md`](docs/openmontage-integration.md) for how
this client relates to the [OpenMontage](https://github.com/calesthio/OpenMontage)
pipeline it was ported from.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests mock all HTTP — they never hit the network or require credentials.
