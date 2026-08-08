---
name: queens-lead-sourcing
description: Actionable workflow for sourcing off-market real estate leads in Queens, NY (pre-foreclosure/lis pendens, probate/estate sales, DOB/HPD building violations, tax lien sale, absentee/long-tenure owners), stacking them into a scored BBL-keyed spreadsheet, skip tracing, and running compliant outreach. Use this whenever the user asks about finding off-market deals, distressed properties, motivated sellers, wholesaling leads, or investment property leads in Queens or NYC — especially Far Rockaway/Bayswater/zip 11691 — or mentions lis pendens, pre-foreclosure, probate leads, DOB/HPD violations, tax lien sale, list stacking, skip tracing, or HETPA. Always run the HETPA compliance gate before drafting any outreach or contract to a distressed-property owner, even if the user doesn't ask for it explicitly — this is a legal requirement, not an optional step.
---

# Queens Off-Market Lead Sourcing

A step-by-step workflow for finding, scoring, and contacting off-market real estate leads in Queens — built around free public-record sources first, paid tools second. The core insight this skill operationalizes: a single distress list is mostly noise, but a property that hits **multiple** lists (probate + violations, absentee + tax delinquent, etc.) is dramatically more likely to convert. The job is to build that overlap, not just pull one list and start dialing.

## Step 0 — HETPA gate (do this before anything else)

Before drafting outreach, a contract, or advising the user to contact any owner, check whether **NY Real Property Law §265-a (Home Equity Theft Prevention Act)** applies. It covers any 1–4 family residence where the owner is:
- in foreclosure, or
- on a tax lien sale list, or
- 2+ months behind on the mortgage *and* the deal involves a reconveyance/repurchase option.

Read [references/hetpa-compliance.md](references/hetpa-compliance.md) for the full checklist and required contract elements before proceeding. Lis pendens leads and tax-lien-sale leads are HETPA-covered by definition — treat them as covered until an attorney's contract package says otherwise. Getting this wrong exposes the user to injunctive relief and up to $25,000 per violation, and voids any liability-limiting clause in their contract, so this isn't a step to skip or soften even under time pressure.

If the user hasn't confirmed they have an attorney-drafted HETPA-compliant contract package yet, say so plainly and steer them to get one before any lis-pendens or tax-lien outreach goes out — don't just generate outreach copy and let the gap pass silently.

## Step 1 — Pick the source(s) to pull

Read [references/data-sources.md](references/data-sources.md) for the full detail per source (URLs, phone numbers, dataset IDs, search parameters, what signals to look for). Summary of the five source categories and when each is most useful:

| Source | Best for | Free? |
|---|---|---|
| Lis pendens / pre-foreclosure | Owner still holds title, most time-sensitive, highest urgency | Yes (NYSCEF, ACRIS) / paid shortcuts exist |
| Probate / estate | Heirs who don't want the property, often out-of-state | Yes (Surrogate's Court + ACRIS cross-ref) |
| DOB/HPD building violations | Deferred maintenance, owner without money/attention | Yes (NYC Open Data CSV/API) |
| Tax lien sale list | Hard deadline, HETPA-covered | Yes (NYC Open Data) |
| Absentee / long-tenure owners | Quiet, no distress, high equity, tired landlords | Paid tools do this at volume (PropertyShark, PropStream) |

Don't just pull the one source the user mentioned — ask (or infer from context) whether they want a single-source pull or want to build toward the multi-source stack in Step 3, since the latter is where the real signal is.

## Step 2 — Pull the data

- **DOB/HPD violations and tax lien sale list**: these have real, queryable APIs (Socrata). Use `scripts/fetch_nyc_violations.py` to pull them as CSV, filtered to a zip code or borough. Socrata dataset IDs get renamed occasionally, so the script has a `--discover` mode that fetches a small sample and prints the actual column names before you commit to a filter — run that first if a filter returns zero rows unexpectedly, rather than assuming the data source is empty. This requires outbound network access to `data.cityofnewyork.us`; if you're running in a sandboxed agent environment that blocks general internet egress, the script will fail with a connection/tunnel error rather than bad data — run it from an environment with network access instead, or fetch the CSV export manually from the dataset's NYC Open Data page.
- **Lis pendens, probate, ACRIS deed/mailing-address lookups**: these don't have a public bulk API. They're single-record or index searches through NYSCEF, ACRIS, and the Surrogate's Court e-filing portal, or a phone call to the Queens County Clerk Block & Lot Clerk (718-298-0612). Walk the user through the search parameters in the reference file, or if you have browser automation available, drive the search yourself and compile results into a CSV with at minimum: BBL (or block+lot), owner/party name, address, filing date.
- **Absentee/long-tenure owners**: this is a paid-tool-at-volume job (PropertyShark, PropStream, BatchLeads). If the user has API/export access to one of these, help them structure the filter (mailing address ≠ property address, tenure 20+ years, no permits in 15+ years, non-owner-occupied 2-4 family). If they don't, say so rather than fabricating a data pull you can't actually perform.

Every CSV you produce or help assemble should carry a **BBL column** (Borough-Block-Lot) — that's the join key for stacking in the next step. If a source only gives block+lot, construct BBL as `borough_code + block.zfill(5) + lot.zfill(4)` (Queens = borough code 4).

## Step 3 — Stack and score

This is the highest-leverage step — skipping it and working single-source lists is the most common mistake. Use `scripts/stack_leads.py` to merge any number of source CSVs (each must have a `bbl` column) into one spreadsheet, scored by how many sources each property hits. Read [references/scoring-worksheet.md](references/scoring-worksheet.md) for the scoring rationale and the specific combinations worth prioritizing (e.g. probate + open violations, absentee + tax delinquent). Work the 3+ hit properties first; they convert at a meaningfully higher rate than any single list.

## Step 4 — Skip trace

Once the stacked list is scored and prioritized, skip trace the top-N owners (start with the highest-scoring 50, per the source playbook's Day 6 target). Free/cheap paths: ACRIS deed owner name + mailing address, then TruePeopleSearch or FastPeopleSearch by hand, or a batch skip-trace service (BatchSkipTracing, PropStream) if the user has an account. This skill doesn't automate skip tracing itself — no free bulk API exists for it — but help structure the input list (name, last known address) so it's ready to feed into whichever tool the user has.

## Step 5 — Outreach

Sequence: direct mail first (3–4 touches over 90 days), then cold calling the skip-traced numbers, then door-knocking the highest-scoring stacked leads. Two compliance notes to actually apply, not just mention:
- **HETPA** (Step 0) governs the *contract*, not just the mailer — if the lead is lis-pendens or tax-lien sourced, don't draft outreach that skips past the disclosure/cancellation-notice requirements as if it were a standard deal.
- **TCPA**: before generating a cold-call or text script, ask whether the numbers have been scrubbed against the National DNC Registry, or default to recommending mail/door-knock only until the user confirms scrubbing or attorney sign-off.

When drafting the actual mailer or call script, keep the message about the *contract terms/timeline*, not the property — that's the compliance-safe framing the source playbook calls out, and it's also just better sales copy for distressed sellers.

## Notes on scope

This skill is Queens/NYC-specific by design (Queens County Clerk, Queens Surrogate's Court, NYC Open Data, ACRIS). If the user asks about a different county or state, the *pattern* (public distress records → BBL/parcel-key stacking → scoring → skip trace → compliant outreach) still applies, but the specific portals, phone numbers, and HETPA-equivalent statute will differ — say so rather than reusing Queens-specific URLs and citations for another jurisdiction.
