# CLAUDE.md — Higgsfield Automation

This file provides guidance for AI assistants (Claude Code and others) working in this repository.

## Project Overview

This repository automates workflows with the [Higgsfield AI](https://higgsfield.ai) platform — an AI-powered video generation and editing service. Typical use cases include:

- Programmatic video generation via the Higgsfield API
- Batch processing pipelines for creative assets
- Scheduling and orchestrating video rendering jobs
- Integrating Higgsfield output into downstream systems (CDNs, social platforms, DAMs)

## Repository Status

Python-based. `src/client.py` holds the single Higgsfield API client; `src/batch.py` and
`scripts/run_batch.py` implement unlimited-generations batch video generation (submit many
jobs at once, poll to completion, persist job IDs for restart recovery). Update this file as
the codebase grows further.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Copy and fill in environment variables
cp .env.example .env
```

## Environment Variables

Add required variables to `.env.example` (never commit real secrets). Expected keys will include:

| Variable | Description |
|---|---|
| `HIGGSFIELD_API_KEY` | Higgsfield API key for authenticated requests |
| `HIGGSFIELD_API_BASE` | API base URL (default: `https://api.higgsfield.ai`) |

## Project Structure

```
.
├── CLAUDE.md              # This file
├── .env.example           # Environment variable template
├── README.md              # User-facing documentation
├── src/
│   ├── client.py          # Single Higgsfield API client (all HTTP calls go through here)
│   ├── batch.py           # BatchRunner: submit + poll batch video generation jobs
│   └── storage.py         # JSON-backed job store for restart recovery
├── scripts/
│   └── run_batch.py       # CLI entry point for batch generation
├── examples/
│   └── prompts.example.json  # Example batch input
└── tests/                 # pytest suite
```

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

```bash
pip install -r requirements-dev.txt
pytest
```

## CI / CD

Document the CI pipeline here once configured. Common things to capture:

- Which checks must pass before merge (lint, type check, tests)
- How deployments are triggered
- Branch protection rules

## Working with the Higgsfield API

Key things to know when implementing against Higgsfield:

- Authentication uses a bearer token (`Authorization: Bearer <HIGGSFIELD_API_KEY>`).
- Video generation jobs are asynchronous — poll the job status endpoint until `status` is `completed` or `failed`.
- Always check `job.status` before downloading output assets.
- Store job IDs persistently so jobs can be recovered after a process restart.
- **Unlimited generations**: our account tier has no per-account generation cap, so batch
  code (`src/batch.py`, `scripts/run_batch.py`) submits every job in a batch up front instead
  of throttling batch size to conserve quota. The API still enforces a per-request rate limit,
  so `HiggsfieldClient` retries `429`s with exponential backoff — that backoff is still
  required and must not be removed.

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
