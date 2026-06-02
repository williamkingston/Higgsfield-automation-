# Higgsfield Automation

Automation workflows for AI-powered video generation and downstream integrations.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # use requirements.txt for runtime only

cp .env.example .env                  # then fill in real values
```

## Environment variables

See `.env.example`. Secrets live in `.env` (gitignored) — never commit real keys.

| Variable | Description |
|---|---|
| `BLOOM_API_KEY` | Bloom API key (prefix `bloom_sk_`) |
| `BLOOM_API_BASE` | Bloom API base URL (default `https://api.bloom.ai`) |

## Bloom API client

All Bloom API calls route through `src/bloom`. It loads credentials from the
environment, sends bearer auth, retries `429` responses with exponential
backoff, and logs request IDs (never the key).

```python
from src.bloom import BloomClient

client = BloomClient()          # reads BLOOM_API_KEY / BLOOM_API_BASE from env
job = client.post("/v1/jobs", json={"prompt": "..."})
status = client.get(f"/v1/jobs/{job['id']}")
```

## Tests

```bash
pytest
```
