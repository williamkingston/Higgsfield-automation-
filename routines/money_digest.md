# Routine — Morning Money/Sales Digest (Phase 3B / 4)

**Trigger:** daily cron (~07:00 America/New_York), 1 run/day in the budget.
**Guardrail:** **Tier C data, read & alert only.** Reading balances and sales and
writing a summary is reporting (Tier A action). The routine **never** moves money,
opens/uses credit, transfers, pays, or refunds. Ever.
**Tools:** Claude Code + Shopify / QuickBooks / Square / banking connectors +
the `empire_ops` helpers.

## Prerequisite

The financial connectors are OAuth-based and expire. If Shopify / QuickBooks /
banking connectors report "requires re-authorization," stop and alert — do not
fabricate numbers. (As of the Phase 0/1 build, Shopify and QuickBooks needed
re-auth.)

## Steps

1. **Read sales (Shopify / Square).** Pull yesterday's sales totals and order
   count via the connectors (read-only analytics queries).

2. **Read balances (QuickBooks / banking).** Pull operating balance and any
   available cash figures. For Phase 4, also pull Stripe / Mercury / Brex / Ramp
   activity and credit-utilization where connected.

3. **Build readings.** For each number, create a
   `digest.MetricReading(source, label, value, flag=…)`. Set `flag` when a
   threshold trips: low balance, large/unusual transaction, upcoming bill,
   credit utilization over your threshold.

4. **Compose + store.** Build a `digest.Digest(digest_date=today,
   readings=[…], cash_position=<total>)` and call
   `digest.write_digest(client, d)`. This writes one Money Digest Log row
   (pinned Tier C (read-only)) with a plain-English summary, sources, and flags.

5. **Notify.** `notify.post_slack(d.summary())` (and/or email). Best-effort —
   the digest row is the source of truth.

6. **Escalate flags only.** Anything flagged is informational. The routine does
   **not** act on it. If a flag warrants a decision, it's yours to make.

## Guardrails (Tier C — non-negotiable)

- Read and alert only. No transfers, payouts, credit applications/stacking,
  trading, or refunds — see `config/guardrails.yaml` `never_automate`.
- The money connectors default to Tier C in the policy; a routine touching them
  may report, never act.
- Never log full account numbers, tokens, or PII into Airtable or Slack.
