# Higgsfield Automation

Batch video generation against the [Higgsfield AI](https://higgsfield.ai) API. Our account
tier has unlimited generations, so the batch runner submits every job in a run up front
instead of throttling batch size — the client still backs off on `429`s to respect the API's
per-request rate limit.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # fill in HIGGSFIELD_API_KEY
```

## Usage

```bash
python -m scripts.run_batch --input examples/prompts.example.json --out-dir output/
```

Submits every prompt in the input file as a video generation job, polls until each job is
`completed` or `failed`, and downloads completed assets into `--out-dir`. Job state is
persisted to `output/jobs.json`, so re-running the same command resumes any jobs still
pending instead of resubmitting them.

## Tests

```bash
pytest
```

See [CLAUDE.md](./CLAUDE.md) for project conventions.
