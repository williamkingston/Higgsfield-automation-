# CLAUDE.md — Higgsfield Automation

Guidance for AI assistants (Claude Code and others) working in this repository.

## Project Overview

This repository automates workflows with the [Higgsfield AI](https://higgsfield.ai) platform — an AI-powered video generation and editing service. Target use cases:

- Programmatic video generation via the Higgsfield API
- Batch processing pipelines for creative assets
- Scheduling and orchestrating video rendering jobs
- Integrating Higgsfield output into downstream systems (CDNs, social platforms, DAMs)

## Repository Status

**Greenfield — no source code yet.** The repo contains only this file. When adding the first code, choose a language/framework and update the sections below accordingly.

## Project Structure

```
.
├── CLAUDE.md            # This file — AI assistant guidance
├── src/                 # Main source code (create when adding first module)
├── tests/               # Test suite (mirror src/ layout)
├── scripts/             # One-off or utility scripts
└── docs/                # Additional documentation
```

Create `.env.example`, `README.md`, and build/config files as needed during initial setup.

## Development Setup

No setup steps yet. When initialising the project, document the exact commands here. Example patterns:

```bash
# Python
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"

# Node/TypeScript
npm install

# Environment variables (always required)
cp .env.example .env   # then fill in real values
```

## Environment Variables

Store secrets in `.env` locally (must be in `.gitignore`). Never commit credentials.

| Variable | Description |
|---|---|
| `HIGGSFIELD_API_KEY` | Bearer token for Higgsfield API |
| `HIGGSFIELD_API_BASE` | API base URL (default `https://api.higgsfield.ai`) |

Add new variables to `.env.example` with placeholder values whenever they are introduced.

## Key Conventions

### Code Style

- Follow the language's idiomatic style (PEP 8 for Python, Prettier for JS/TS).
- Keep functions small and single-purpose.
- No comments that describe *what* — only comment *why* when non-obvious.
- No half-finished implementations; every committed function must be callable.

### Higgsfield API Integration

- **Single client module:** All Higgsfield API calls go through one module (e.g. `src/client.py` or `src/api/client.ts`). Never scatter raw HTTP calls.
- **Auth:** Bearer token via `Authorization: Bearer <HIGGSFIELD_API_KEY>`.
- **Async jobs:** Video generation is asynchronous — poll the job status endpoint until `status` is `completed` or `failed`. Always check status before downloading assets.
- **Rate limits:** Implement exponential backoff on `429` responses.
- **Logging:** Log API request IDs for traceability. Never log API keys or response bodies that may contain PII.
- **Job persistence:** Store job IDs so jobs survive process restarts.

### Error Handling

- Validate at system boundaries (API responses, user input, file I/O).
- No defensive checks for impossible internal conditions.
- Prefer descriptive errors over silent fallbacks.

### Secrets

- Never commit credentials, API keys, or tokens.
- `.env` for local dev; environment variables in CI/CD.
- `.env` must be in `.gitignore`.

## Running Tests

No test framework chosen yet. When one is added, put the exact command here:

```bash
# pytest / npm test / etc.
```

## CI / CD

Not yet configured. Document here once set up: required checks, deployment triggers, branch protection.

## Git Workflow

- Develop on feature branches; open PRs against `main`.
- Imperative commit messages: `Add retry logic for video polling`.
- One logical change per commit.
- No force-pushes to `main` or shared branches.

## Adding New Features

1. Branch from `main`.
2. Write tests alongside implementation.
3. Update this `CLAUDE.md` if the change introduces new conventions, directories, or env vars.
4. PR → CI green → merge.
