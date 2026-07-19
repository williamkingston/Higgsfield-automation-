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
into per-scene generation jobs. `src/apilayer/` adds clients for APILayer's
family of data/enrichment APIs (weather, geocoding, screenshots, ...) that can
feed real-world context into that pipeline's scenes (see "APILayer Clients"
below). Update this file as the codebase grows.

Alongside the Python pipeline, the repo also carries a set of Claude Code
**agent skills** under `.agents/skills/` (see "Agent Skills" below) used when
an AI assistant works in this repo — for authoring HyperFrames/GSAP video
compositions, scraping reference material, and reviewing UI/animation polish.
These are Markdown instructions and reference docs, not application code.

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
| `LOVART_ACCESS_KEY` | Lovart access key (`ak_...`); identifies the account |
| `LOVART_SECRET_KEY` | Lovart secret key (`sk_...`); used to HMAC-sign requests, sensitive, never log or commit |
| `LOVART_API_BASE` | Lovart API base URL (default: `https://lgw.lovart.ai`) |
| `LOVART_API_PREFIX` | Lovart OpenAPI path prefix (default: `/v1/openapi`) |
| `{PRODUCT}_ACCESS_KEY` | Access key for one APILayer product, e.g. `WEATHERSTACK_ACCESS_KEY` (see `.env.example` for the full list and "APILayer Clients" below) |

### Lovart client

All Lovart calls go through `src/lovart/` (`LovartClient`). It loads credentials
via `LovartConfig.from_env()` and **HMAC-SHA256-signs every request**: the
signature is computed over `"{METHOD}\n{PATH}\n{TIMESTAMP}"` keyed by the secret
key and sent with the access key, timestamp, and signed method/path as headers
(`X-Access-Key`, `X-Timestamp`, `X-Signature`, `X-Signed-Method`,
`X-Signed-Path`). All signing lives in `LovartClient._signed_headers`. The client
retries on `429`/`5xx` with exponential backoff (honoring `Retry-After`).

Generation is a chat-thread flow: `chat(prompt, project_id)` returns a
`thread_id`, `get_status` reports `running`/`done`/`abort`, and `get_result`
returns artifacts. `generate()` ties these together (submit → poll → result,
with optional `auto_confirm` for high-cost operations). Other methods cover
projects (`create_project`, `rename_project`, `validate_project`) and billing
mode (`query_mode`, `set_mode`).

- `scripts/lovart_generate.py` — single-prompt example.
- `scripts/lovart_batch.py` — batch-generate from a `.txt`/`.csv` of prompts,
  writing a JSON manifest of results.

## APILayer Clients

[APILayer](https://apilayer.com) publishes dozens of independent single-purpose
REST APIs (weather, currency, geocoding, screenshots, validation, ...) that all
share the same two conventions: an `access_key` query parameter for auth, and a
JSON failure envelope of `{"success": false, "error": {"code", "type", "info"}}`.
`src/apilayer/base.py` implements that shared contract exactly once
(`APILayerClient`/`APILayerConfig`) — retries with backoff on `429`/`5xx`,
error parsing — so every product module only declares its base URL and typed
endpoint methods. Each product is signed up for and billed independently, so
each client reads its own `{SERVICE}_ACCESS_KEY` / `{SERVICE}_API_BASE` env
vars (see `.env.example`) rather than sharing one key.

Product clients, one module each under `src/apilayer/`: `weatherstack`
(weather), `aviationstack` (flights), `fixer` / `currencylayer` (FX rates),
`marketstack` (stocks), `positionstack` (geocoding), `ipstack` (IP
geolocation), `vatlayer` (VAT validation), `mailboxlayer` (email validation),
`numverify` (phone validation), `userstack` (user-agent detection), `serpstack`
(search results), `scrapestack` (web scraping proxy), `screenshotlayer`
(website screenshots), `giflayer` (video → GIF), `pdflayer` (HTML/URL → PDF),
`coinlayer` (crypto rates), `mediastack` (news), `streetlayer` (address
autocomplete/validation).

Most methods return the parsed JSON body via `request()`. A few return raw
bytes/text via `request_raw()` for products whose success response isn't JSON
(`screenshotlayer.capture`, `pdflayer.convert_url`/`convert_html`,
`scrapestack.scrape`).

`src/apilayer/enrichment.py` is the glue to the episodic pipeline: it's **not**
wired into `EpisodePipeline` automatically — call `enrich_with_weather` /
`enrich_with_site_capture` (or the generic `attach_enrichment`) explicitly
before generation for scenes that should reflect external data. Results land
in `scene.params["enrichment"]`, available to prompt templates. Add more
`enrich_with_*` helpers the same way as new products are wired into scenes;
don't build a generic dispatcher for all 19 clients up front.

## Project Structure

```
.
├── CLAUDE.md                  # This file
├── README.md                  # User-facing documentation
├── pyproject.toml             # Project metadata & dependencies (uv-managed)
├── uv.lock                    # Pinned dependency versions (committed)
├── .python-version            # Python version pin for uv
├── setup.sh                   # Bootstrap script (installs uv + syncs env)
├── setup-ltx.sh               # Clones/installs Lightricks/LTX-Video for the local `ltx` backend (needs an NVIDIA GPU)
├── setup-hyperframes.sh       # Installs the HyperFrames skill set into another repo's .agents/skills/
├── skills-lock.json           # Tracks vendored agent skills (source repo + content hash)
├── .env.example               # Environment variable template
├── .github/workflows/ci.yml   # CI: uv sync, ruff check, pytest
├── src/higgsfield/            # The Higgsfield package
│   ├── client.py              # HiggsfieldClient — the single API entry point
│   ├── config.py              # HiggsfieldConfig.from_env() + resolve_output_dir()
│   ├── errors.py              # Typed exceptions
│   ├── models.py              # Series / Episode / Scene (YAML-loaded)
│   ├── backends.py            # Higgsfield (API) and LTX-Video (local) backends
│   ├── pipeline.py            # EpisodePipeline — generate + persist + assemble
│   └── assemble.py            # ffmpeg concat of an episode's clips
├── src/lovart/                # LovartClient — HMAC-signed chat-thread generation (see below)
├── src/apilayer/              # APILayer product clients — see "APILayer Clients" below
├── series/                    # Episode/series definitions (YAML) + the Mythrealm show bible
├── assets/                    # Reference art for the Mythrealm series (characters/, creatures/, keyart/, lore/)
├── tests/                     # Test suite (offline, no API key needed)
├── scripts/
│   ├── generate_video.py      # Runnable example: submit one job and wait
│   ├── generate_episode.py    # Generate a full episode from a series YAML
│   ├── lovart_generate.py     # Single-prompt Lovart example
│   └── lovart_batch.py        # Batch-generate from a .txt/.csv of prompts
└── .agents/skills/            # Claude Code agent skills — see "Agent Skills" below
```

All API access goes through `HiggsfieldClient` (`src/higgsfield/client.py`):
bearer auth, exponential backoff on `429`/`5xx` (honoring `Retry-After`),
request-id logging, and the submit-then-poll job pattern via
`create_generation` → `wait_for_job` (or the combined `generate_and_wait`). The
episodic pipeline builds on this client through the `HiggsfieldBackend`.

## Mythrealm Series & Assets

`series/mythrealm-bible.md` is the canon source of truth for **Mythrealm**, a
creature-bonding saga (young "Tamers" bonding with "Mythra" creatures via
Relics) used as the example content for the episodic pipeline. Episode scripts
in `series/*.yaml` (e.g. `mythrealm.yaml`, `the-emberwright.yaml`) draw their
world, cast, and creature designs from the bible. Visual references live in
`assets/characters/`, `assets/creatures/`, `assets/keyart/`, and
`assets/lore/` — treat these as reference material for prompts, not code.

## Agent Skills

`.agents/skills/` holds Claude Code skills used when an AI assistant works in
this repo (or is installed elsewhere via `setup-hyperframes.sh`):

- `hyperframes` — author HyperFrames HTML/GSAP video compositions: timing,
  captions, transitions, audio-reactive animation, house style and palettes.
- `gsap` — GSAP animation reference (tweens, timelines, easing) scoped to the
  HyperFrames runtime contract.
- `remotion-to-hyperframes` — migrates existing Remotion (React) video
  projects into HyperFrames, with an SSIM-graded tiered test corpus guarding
  against lossy translations.
- `website-to-hyperframes` — a 7-step pipeline that captures a website and
  produces a HyperFrames promo/product video from it; ships a bundled SFX
  library under `assets/sfx/`.
- `emil-design-eng` — UI/animation polish review philosophy (vendored from
  `emilkowalski/skill`).
- `just-scrape` — web search/scrape/crawl/monitor via the ScrapeGraph AI CLI
  (vendored from `scrapegraphai/just-scrape`; needs the `just-scrape` CLI and
  `SGAI_API_KEY`).

`emil-design-eng` and `just-scrape` are vendored via `npx skills add` and
tracked in `skills-lock.json` (source repo, path, content hash) — prefer
updating at the source and re-pulling over editing them directly.

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
