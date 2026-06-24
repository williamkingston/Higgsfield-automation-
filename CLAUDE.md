# CLAUDE.md — Higgsfield Automation

This file provides guidance for AI assistants (Claude Code and others) working in this repository.

## Project Overview

This repository automates workflows with the [Higgsfield AI](https://higgsfield.ai) platform — an AI-powered video generation and editing service. Typical use cases include:

- Programmatic video generation via the Higgsfield API
- Batch processing pipelines for creative assets
- Scheduling and orchestrating video rendering jobs
- Integrating Higgsfield output into downstream systems (CDNs, social platforms, DAMs)

## Repository Status

The core `HiggsfieldClient` foundation is in place (`src/higgsfield/`), with an
offline test suite. On top of it sits an episodic video pipeline (`models.py`,
`backends.py`, `pipeline.py`, `assemble.py`) that turns a YAML-defined series
into per-scene generation jobs. Update this file as the codebase grows.

## Development Setup

This project uses [uv](https://docs.astral.sh/uv/) to manage the Python
environment and dependencies. The fastest path is the bootstrap script, which
installs uv (if missing), syncs the environment, and scaffolds `.env`:

```bash
./setup.sh
```

To do it manually:

```bash
# Install uv (one-time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create .venv and install all deps (incl. dev) from pyproject.toml / uv.lock
uv sync --extra dev

# Copy and fill in environment variables
cp .env.example .env   # then set HIGGSFIELD_API_KEY
```

Run commands inside the environment with `uv run` (no manual activation needed):

```bash
uv run pytest          # tests
uv run ruff check .    # lint
uv run ruff format .   # format
```

Dependencies are declared in `pyproject.toml` and pinned in `uv.lock` (committed
for reproducible installs). Add a runtime dependency with `uv add <pkg>` and a
dev-only one with `uv add --dev <pkg>`.

## Environment Variables

Add required variables to `.env.example` (never commit real secrets). Expected keys will include:

| Variable | Description |
|---|---|
| `HIGGSFIELD_API_KEY` | Higgsfield API key for authenticated requests |
| `HIGGSFIELD_API_BASE` | API base URL (default: `https://api.higgsfield.ai`) |
| `LOVART_API_KEY` | Lovart API key, sent as the `X-API-Key` header; sensitive, never log or commit |
| `LOVART_API_BASE` | Lovart API base URL (default: `https://api.lovart.ai`) |

### Lovart client

All Lovart calls go through `src/lovart/` (`LovartClient`). It loads the API key
via `LovartConfig.from_env()`, authenticates each request with the `X-API-Key`
header, retries on `429`/`5xx` with exponential backoff, and supports the async
submit-then-poll job pattern (`create_generation` → `wait_for_job`). The auth
scheme lives in one place (`LovartClient._auth_headers`) so it can be adjusted if
your Lovart account's requirements differ. See `scripts/lovart_generate.py` for a
runnable example.

## Project Structure

```
.
├── CLAUDE.md                  # This file
├── pyproject.toml             # Project metadata & dependencies (uv-managed)
├── uv.lock                    # Pinned dependency versions (committed)
├── .python-version            # Python version pin for uv
├── setup.sh                   # Bootstrap script (installs uv + syncs env)
├── .env.example               # Environment variable template
├── src/higgsfield/            # The Higgsfield package
│   ├── client.py              # HiggsfieldClient — the single API entry point
│   ├── config.py              # HiggsfieldConfig.from_env() + resolve_output_dir()
│   ├── errors.py              # Typed exceptions
│   ├── models.py              # Series / Episode / Scene (YAML-loaded)
│   ├── backends.py            # Higgsfield (API) and LTX-Video (local) backends
│   ├── pipeline.py            # EpisodePipeline — generate + persist + assemble
│   └── assemble.py            # ffmpeg concat of an episode's clips
├── series/                    # Example series definitions (YAML)
├── tests/                     # Test suite (offline, no API key needed)
└── scripts/
    ├── generate_video.py      # Runnable example: submit one job and wait
    └── generate_episode.py    # Generate a full episode from a series YAML
```

All API access goes through `HiggsfieldClient` (`src/higgsfield/client.py`):
bearer auth, exponential backoff on `429`/`5xx` (honoring `Retry-After`),
request-id logging, and the submit-then-poll job pattern via
`create_generation` → `wait_for_job` (or the combined `generate_and_wait`). The
episodic pipeline builds on this client through the `HiggsfieldBackend`.

## Key Conventions

### Code Style

- Follow the language's idiomatic style (PEP 8 for Python, Prettier defaults for JS/TS).
- Keep functions small and single-purpose.
- Avoid adding comments that describe *what* code does — only comment *why* when the reason is non-obvious.
- No half-finished implementations; every committed function should be callable.

### API Interactions

- All Higgsfield API calls must go through a single client module (e.g., `src/client.py` or `src/api/client.ts`). Never scatter raw `requests`/`fetch` calls across the codebase.
- Respect rate limits; implement exponential backoff on `429` responses.
- Log API request IDs for traceability, never log API keys or full response bodies that may contain PII.

### Error Handling

- Validate at system boundaries (API responses, user input, file I/O).
- Don't add defensive checks for conditions that genuinely cannot occur inside well-controlled internal code.
- Prefer raising/throwing descriptive errors over silent fallbacks.

### Secrets

- Never commit credentials, API keys, or tokens.
- Use `.env` locally and environment variables in CI/CD.
- `.env` must be in `.gitignore`.

## Running Tests

Tests run under pytest, inside the uv-managed environment:

```bash
uv run pytest
```

Tests run fully offline — the HTTP session is faked, so no API key or network
access is required.

## CI / CD

GitHub Actions runs on every push to `main` and on every pull request
(`.github/workflows/ci.yml`): it syncs the uv environment (`uv sync --extra
dev`), lints with `uv run ruff check .`, and runs `uv run pytest`. Both lint and
tests must pass before merge.

## Working with the Higgsfield API

Key things to know when implementing against Higgsfield:

- Authentication uses a bearer token (`Authorization: Bearer <HIGGSFIELD_API_KEY>`).
- Video generation jobs are asynchronous — poll the job status endpoint until `status` is `completed` or `failed`.
- Always check `job.status` before downloading output assets.
- Store job IDs persistently so jobs can be recovered after a process restart.

## Git Workflow

- Develop on feature branches; open PRs against `main`.
- Write clear, imperative commit messages: `Add retry logic for video polling`.
- Keep commits atomic — one logical change per commit.
- Do not force-push to `main` or shared branches.

## Adding New Features

1. Create a feature branch from `main`.
2. Write tests alongside the implementation.
3. Update this `CLAUDE.md` if the change introduces new conventions, directories, or environment variables.
4. Open a PR and ensure CI passes before merging.
