# Velvyt Empire — End-to-End Automation Plan

A staged build plan for turning the connector + Claude Code + Higgsfield/Suno
stack into real, mostly-unattended automation across the ventures — without
burning capital or risking the money/credit side.

> **Status:** Phase 0 shipped (live Empire Ops base, verified loop, enforced
> guardrails). Phases 1 (content engine), 2 (music pipeline), 3B (money digest),
> and the Phase 5 lead loop are built as tested `empire_ops` helpers + routine
> playbooks, pending credentials / connector re-auth for live runs. See
> `routines/` and `src/empire_ops/`.

---

## 1. The one rule that makes this work

You don't automate the empire in one shot. You build **one proven loop**, then
clone the pattern. Every phase ships a working, guardrailed loop before the next
starts. If a phase doesn't save real hours, you stop and fix it before expanding.

## 2. Architecture — four layers

```
TRIGGER          →   EXECUTION         →   STORAGE/STATE      →   GUARDRAIL
Claude Code          Claude Code +         Airtable "Empire Ops"   Approval gates
  Routines             skill files          (queues, calendars)     in Airtable
  (cron/webhook)     MCP connectors        Cloudinary (assets)     Human-in-loop on
Zapier / Composio    Playwright MCP        Supabase (app data)       money/credit/legal
```

- **Trigger:** Claude Code Routines (primary, ~15 runs/day). Zapier/Composio for
  no-code app triggers.
- **Execution:** Claude Code + skills (Suno Bible, Higgsfield pipeline,
  cinema-worldbuilder, banana-pro-director) + MCP connectors + Playwright.
- **State:** One Airtable base is the brain. Cloudinary holds assets;
  Supabase/Base44 holds app data.
- **Guardrail:** Nothing publishes or moves money without a gate (§4).

## 3. The 15-runs/day budget

| Runs/day | Routine |
|---|---|
| 1 | Nightly content generation (all brands queued together) |
| 1 | Music catalog sync + render queue |
| 1 | Morning money/sales digest (read-only) |
| 1 | Shopify drop-prep (Wrich Velvyt) |
| 1 | Ad-performance pull (Motion/Supermetrics) |
| 2–3 | Webhook-triggered (new order, new lead) |
| ~6–8 | Headroom / manual triggers / retries |

Batch ventures into shared routines. Managed Agents only enter in Phase 6.

## 4. Guardrail policy — non-negotiable

Encoded in `config/guardrails.yaml` and enforced by `src/empire_ops/guardrails.py`.

- **Tier A — fully automate** (safe, reversible): asset tagging/storage, data
  syncing, reporting/digests, draft generation, catalog/calendar updates.
- **Tier B — automate to a draft, you approve:** anything published under Wr!ch
  Velvyt or your name, music releases, ad-spend changes, customer-facing copy,
  social posts. Agent does 90%; you hit send from the Needs Approval view.
- **Tier C — never automate:** money movement, credit applications/stacking,
  brokerage/trading, contracts/legal, refunds. Agents may *read and alert* —
  never act.

## 5. Phased roadmap

- **Phase 0 — Foundation** ✅ Airtable base + naming/folders + hello-world routine
  + guardrail tiers locked in.
- **Phase 1 — Content engine** (the multiplier): Content Queue → Higgsfield →
  Cloudinary → Needs Approval. Tier B.
- **Phase 2 — Music pipeline:** Music Catalog → Splice beds → Suno scaffolds
  (open verses) → cover-art queue → Drive + Needs Approval. Tier B.
- **Phase 3 — Commerce + reporting:** (A) Wrich Velvyt drop-prep → draft Shopify
  listing → Needs Approval (Tier B). (B) Morning sales/cash digest → Money Digest
  Log (Tier A read-only).
- **Phase 4 — Money ops (read + alert only):** aggregate Stripe/Mercury/Brex/Ramp
  → categorize → flag anomalies/low balances/credit thresholds → alert.
  **Tier C — no transfers, payouts, or credit actions, ever.**
- **Phase 5 — Other ventures:** House of Sweet Things, YvesBnB, Ray's Elite
  Transport, Wrich Big Tech — clone existing loops as each is ready.
- **Phase 6 — Orchestration:** graduate one proven loop to Managed Agents
  (Planner → Generator → Evaluator) only when it clearly earns the cost.

## 6. What stays manual forever

Moving/withdrawing money; applying for or managing credit; signing contracts or
anything legal; final publish/release under your brand or name; anything touching
customer payment or refunds. Automation drafts and alerts — it never acts.

## 7. Success metrics

- Hours saved/week per loop (if < 2 hrs, fix or kill it).
- Approval throughput — how fast Needs Approval clears.
- Zero Tier-C incidents — no automated money/credit/legal action, ever.
- Cost per output stays inside the subscription until a loop earns more.

## 8. First build order

1. **Phase 0** Airtable base + hello-world routine ✅
2. Phase 1 content loop (nightly, Tier B)
3. Phase 3B money/sales digest (read-only — quick win, high signal)
4. Phase 2 music pipeline
5. Everything else, in roadmap order

Build one. Prove it saves hours. Then clone.
