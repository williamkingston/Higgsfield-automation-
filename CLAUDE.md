# CLAUDE.md — Higgsfield Automation

This file provides guidance for AI assistants (Claude Code and others) working in this repository.

## Project Overview

This repository automates workflows with the [Higgsfield AI](https://higgsfield.ai) platform — an AI-powered video generation and editing service. Target use cases:

- Programmatic video generation via the Higgsfield API
- Batch processing pipelines for creative assets
- Scheduling and orchestrating video rendering jobs
- Integrating Higgsfield output into downstream systems (CDNs, social platforms, DAMs)

## Repository Status

**As of 2026-05-24, this repository is in bootstrapping phase.** There is no source code, no dependency files, and no CI configuration yet. The only file is this `CLAUDE.md`.

When adding the first code, you will need to:
1. Choose a language/runtime (Python or Node.js recommended).
2. Initialize the project (`pip init` / `npm init` / `pyproject.toml`).
3. Create `.gitignore` (must include `.env`, `__pycache__/`, `node_modules/`, `.venv/`).
4. Create `.env.example` with placeholder keys.
5. Set up the directory structure below.
6. Update this file to reflect choices made.

## Development Setup

Once the project is initialized, setup should follow this pattern:

```bash
# Python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # or: pip install -e ".[dev]"

# Node / TypeScript
npm install

# Environment
cp .env.example .env
# Fill in HIGGSFIELD_API_KEY and any other required values
```

## Environment Variables

Store in `.env` locally (never commit). Provide a `.env.example` template with empty values.

| Variable | Required | Description |
|---|---|---|
| `HIGGSFIELD_API_KEY` | Yes | Bearer token for Higgsfield API authentication |
| `HIGGSFIELD_API_BASE` | No | API base URL (default: `https://api.higgsfield.ai`) |

Add new variables to this table and to `.env.example` whenever they are introduced.

## Project Structure (target layout)

None of these directories exist yet. Create them as needed:

```
.
├── CLAUDE.md            # AI assistant guidance (this file)
├── .env.example         # Environment variable template (create first)
├── .gitignore           # Must include .env, secrets, build artifacts (create first)
├── README.md            # User-facing documentation
├── src/                 # Main source code
│   ├── client.py        # (or src/api/client.ts) — single Higgsfield API client
│   └── ...
├── tests/               # Test suite
├── scripts/             # One-off or utility scripts
└── docs/                # Additional documentation
```

## Key Conventions

### Code Style

- Follow the language's idiomatic style (PEP 8 for Python, Prettier defaults for JS/TS).
- Keep functions small and single-purpose.
- No comments that describe *what* — only comment *why* when non-obvious.
- No half-finished implementations; every committed function should be callable.
- No premature abstractions; prefer simple, direct code.

### API Client Architecture

- **Single client module**: All Higgsfield API calls must go through one client module (`src/client.py` or `src/api/client.ts`). Never scatter raw HTTP calls across the codebase.
- **Rate limiting**: Implement exponential backoff on `429` responses. Start at 1 second, cap at 60 seconds.
- **Logging**: Log API request IDs for traceability. Never log API keys or full response bodies that may contain PII.
- **Timeouts**: Set explicit request timeouts (recommended: 30s for standard calls, 300s for video generation).

### Error Handling

- Validate at system boundaries (API responses, user input, file I/O).
- Don't add defensive checks for conditions that cannot occur in well-controlled internal code.
- Prefer raising/throwing descriptive errors over silent fallbacks.
- Wrap Higgsfield API errors in a custom exception type that preserves the original status code and request ID.

### Secrets

- **Never commit** credentials, API keys, or tokens.
- Use `.env` locally and environment variables in CI/CD.
- `.env` must be in `.gitignore`.
- If a `.env` file is detected in staged changes, abort the commit.

## Running Tests

No test framework is configured yet. When adding one:

```bash
# Python — use pytest
pytest

# Node — use the test script from package.json
npm test
```

Write tests alongside every new module. Aim for coverage of API client methods and any data transformation logic.

## CI / CD

No CI pipeline is configured yet. When adding one, ensure these checks run on every PR:

- Lint / format check
- Type checking (mypy / tsc)
- Full test suite
- Secret scanning (no `.env` or key patterns in committed files)

## Working with the Higgsfield API

### Authentication

```
Authorization: Bearer <HIGGSFIELD_API_KEY>
```

### Async Job Pattern

Video generation is asynchronous. The standard workflow:

1. **Submit** a generation request → receive a `job_id`.
2. **Poll** the job status endpoint until `status` is `completed` or `failed`.
3. **Check** `job.status` before downloading output assets.
4. **Persist** job IDs so jobs can be recovered after a process restart.

When polling:
- Use exponential backoff (start 2s, cap 30s).
- Set a maximum poll duration (recommended: 10 minutes) and fail explicitly if exceeded.
- Log each poll attempt at debug level.

### Error Responses

Expect standard HTTP error codes from the API. Handle at minimum:
- `401` — invalid or expired API key
- `429` — rate limited, back off and retry
- `500`/`502`/`503` — transient server errors, retry with backoff (max 3 retries)

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
