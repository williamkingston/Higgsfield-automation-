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

Generation runs through the **Higgsfield MCP connector**, authorized per-session
via OAuth in the agent client — **not** via API keys. So there are normally no
secrets to set. `requests` is used only to download finished result URLs.

See `docs/openmontage-integration.md` for why the earlier REST/key approach was
replaced after live validation showed its model ids didn't match the real catalog.

## Project Structure

Update this section as directories are created:

```
.
├── CLAUDE.md            # This file
├── .env.example         # Env template (connector uses OAuth; usually empty)
├── requirements.txt     # Runtime dependencies (requests, for downloads)
├── README.md            # User-facing documentation
├── src/
│   ├── models.py        # Verified Higgsfield model registry
│   ├── client.py        # HiggsfieldConnectorClient (transport-injected)
│   └── batch.py         # Resumable batch runner
├── scripts/run_batch.py # Validate jobs → emit connector payloads
├── tests/               # Test suite (pytest; fake invoker, no network)
├── docs/                # Additional documentation
└── .agents/skills/      # Vendored agent skills (impeccable, taste, OpenMontage, …)
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

- Generation goes through the Higgsfield MCP connector (`generate_video`,
  `job_display`, `show_generations`). `src/client.py` builds/validates the
  requests; the connector call is injected via an `invoker` (agent-driven).
- Use real catalog model ids (`seedance_2_0`, `kling3_0`, `veo3_1`, …) from
  `src/models.py`. Dotted names like `seedance_2.0` are invalid.
- `generate_video` with `get_cost: true` preflights credits **without** creating
  a job — use it before spending.
- Video generation jobs are asynchronous — poll until `status` is terminal.
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
