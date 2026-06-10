# Empire Ops — live Airtable base

The state layer for all automation. One base is the brain: every queue, calendar,
and status lives here.

- **Base name:** Empire Ops
- **Base ID:** `applx48uo2056erUB`
- **Workspace:** My First Workspace (`wspEQoP39aXHTi5NL`)

Routines reference everything by **ID** (see `src/empire_ops/schema.py`) so
renaming a column in the UI never breaks code. If you change the schema,
regenerate that file from `list_tables_for_base` and update the table below.

## Tables

| Table | ID | Purpose | Tier |
|---|---|---|---|
| Content Queue | `tbl7xBGNGjUTaalMN` | Phase 1 — pre-filled prompts → Higgsfield → Cloudinary → Needs Approval | B |
| Music Catalog | `tblzrCOp4c9O7fChh` | Phase 2 — Suno scaffolds (open verses), BPM/key/direction, cover-art queue | B |
| Drop Calendar | `tblNRn8TJ5MOadYtz` | Cross-brand release scheduling | A (publish stays B) |
| Leads | `tblIlXb2ygjyN5lFZ` | Phase 5 — lead intake → drafted response | B |
| Money Digest Log | `tblqZlbdD5zjsIGD6` | Phase 3B/4 — read-only money pulse + flags | **C (read/alert only)** |
| Needs Approval | `tblkmcJDeZgMTCl7j` | Central human-in-loop queue | gate |

## Guardrail tiers baked into the schema

Every table that a routine writes to carries a **Guardrail Tier** field (A/B/C),
mirroring `config/guardrails.yaml`. The Money Digest Log is fixed at **Tier C** —
routines aggregate and summarize, they never move money, touch credit, or act.

## Working with the base

- All reads/writes go through the single client: `src/empire_ops/airtable.py`.
- A row may escalate its tier (B→C) but a routine must never de-escalate one.
- Tier B output always lands in **Needs Approval** with a preview link; a human
  approves before anything publishes.

## Phase 0 smoke test

A row titled `hello-world-heartbeat` exists in Content Queue, created to verify
the read/write loop. Safe to delete once you've confirmed the routine runs.
