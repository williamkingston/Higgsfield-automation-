# Routines

The trigger/execution layer. Two styles, by need:

- **Python routines** (`*.py`) — deterministic jobs that only need the Airtable
  REST API. Run anywhere (cron, CI, a scheduled shell). `hello_world.py` is the
  Phase 0 reference.
- **Playbooks** (`*.md`) — scheduled Claude Code Routines that need the authed
  MCP connectors (Higgsfield, Cloudinary, Shopify, QuickBooks…). A scheduled
  Claude session follows the steps and calls the deterministic `empire_ops`
  helpers (`content`, `approvals`, `digest`, `notify`) for everything that must
  be exact. This keeps OAuth/credit-bearing work on the authed connectors
  instead of fragile hand-rolled clients.

## Schedule (within the ~15 runs/day budget)

| When | Routine | File | Tier |
|---|---|---|---|
| nightly ~02:00 ET | Content engine | `nightly_content.md` | B (draft → approve) |
| nightly (shares slot) | Music pipeline | `music_pipeline.md` | B (scaffold → approve) |
| daily ~07:00 ET | Money/sales digest | `money_digest.md` | C data, read/alert only |
| webhook / sweep | Lead intake | `lead_intake.md` | B (draft + hold → approve) |
| on demand | Foundation check | `hello_world.py` | A |

Batch ventures into shared routines rather than one-per-venture. Leave headroom
for webhook triggers and retries.

## Guardrails

Every routine loads the §4 tiers (`config/guardrails.yaml`) and runs each action
through `empire_ops.guardrails`. Tier B output goes to **Needs Approval**; Tier C
(money/credit/legal) is **read and alert only** — the helpers refuse to queue a
Tier-C item as actionable.
