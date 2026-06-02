# Higgsfield Automation — Velvyt Empire Ops

Automation foundation for the Velvyt ventures: a staged build plan that turns the
Claude Code + Higgsfield/Suno + MCP-connector stack into proven, guardrailed,
mostly-unattended loops. Full plan: [`docs/automation-plan.md`](docs/automation-plan.md).

The guiding rule: **build one proven loop, then clone the pattern.** Nothing
publishes or moves money without a gate.

## Status — Phase 0 (Foundation) shipped

- ✅ **Empire Ops** Airtable base is live (`applx48uo2056erUB`) with all six
  tables — see [`docs/empire-ops-base.md`](docs/empire-ops-base.md).
- ✅ Read/write loop verified against the live base.
- ✅ Guardrail tiers (§4) encoded in [`config/guardrails.yaml`](config/guardrails.yaml)
  and enforced by `src/empire_ops/guardrails.py` (tested).
- ✅ Single Airtable client, env config, and a hello-world routine.

## Layout

```
.
├── config/guardrails.yaml      # §4 tier policy, machine-readable & enforced
├── docs/
│   ├── automation-plan.md      # the staged roadmap
│   └── empire-ops-base.md      # live base IDs + schema reference
├── routines/
│   └── hello_world.py          # Phase 0: read a row, write back
├── src/empire_ops/
│   ├── airtable.py             # the single Airtable client (all base I/O)
│   ├── config.py               # env loading + validation
│   ├── guardrails.py           # tier enforcement (A/B/C)
│   └── schema.py               # live table/field IDs
├── tests/test_guardrails.py
└── .agents/skills/             # HyperFrames skill set (creative execution)
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then fill in AIRTABLE_API_KEY
```

The Airtable token needs `data.records:read`, `data.records:write`, and
`schema.bases:read` on the Empire Ops base. `AIRTABLE_BASE_ID` defaults to the
live base, so only the key is strictly required for Phase 0.

## Run the Phase 0 routine

```bash
python -m routines.hello_world
```

Reads the oldest Content Queue row, checks its guardrail tier, and stamps a
heartbeat into Notes — confirming scheduling, auth, the guardrail tiers, and the
client all work. Tier C rows are read-only and never written.

## Tests

```bash
pytest
```

## Guardrails (read before adding a routine)

| Tier | Meaning | Routine behavior |
|---|---|---|
| A | Fully automate | Acts directly (tagging, syncing, reporting, drafts) |
| B | Draft + approve | Acts, then lands in **Needs Approval** for a human |
| C | Never automate | **Read & alert only** — money, credit, legal, refunds |

Every routine calls `guardrails.check()` / `enforce()` before acting. See §4 of
the plan and `config/guardrails.yaml`.
