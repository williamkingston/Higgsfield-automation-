# CLAUDE.md — Higgsfield Automation

This file provides guidance for AI assistants (Claude Code and others) working in this repository.

## Project Overview

This repository automates workflows with the [Higgsfield AI](https://higgsfield.ai) platform — an AI-powered video generation and editing service. Typical use cases include:

- Programmatic video generation via the Higgsfield API
- Batch processing pipelines for creative assets
- Scheduling and orchestrating video rendering jobs
- Integrating Higgsfield output into downstream systems (CDNs, social platforms, DAMs)

## Repository Status

This repository is new and currently empty. Update this file as the codebase grows.

## Development Setup

Document the setup steps here once the project is initialised. Common patterns:

```bash
# Python projects
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # or: pip install -e ".[dev]"

# Node projects
npm install

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

Update this section as directories are created:

```
.
├── CLAUDE.md            # This file
├── .env.example         # Environment variable template
├── README.md            # User-facing documentation
├── src/                 # Main source code
├── tests/               # Test suite
├── scripts/             # One-off or utility scripts
└── docs/                # Additional documentation
    └── guides/          # Step-by-step workflow guides
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

Document test commands here once a test framework is chosen:

```bash
# Python (pytest)
pytest

# JavaScript/TypeScript
npm test
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
