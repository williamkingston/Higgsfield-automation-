# Routine — Nightly Content Engine (Phase 1)

**Trigger:** nightly cron (~02:00 America/New_York), 1 run/day in the budget.
**Guardrail:** Tier B — generate drafts only. **Nothing posts.** Every output
lands in Needs Approval for a human.
**Tools:** Claude Code + Higgsfield connector + Cloudinary connector + the
`empire_ops` helpers.

This is a Claude Code Routine: a scheduled session runs these steps using the
authed MCP connectors, leaning on the deterministic `empire_ops` helpers for all
Airtable I/O and the guardrail check.

## Steps

1. **Select work.** Call `content.ready_rows(client)` to get Content Queue rows
   that are `Queued` and due (`Scheduled For` empty or ≤ today). If none, log
   "nothing due" and stop. Cap the batch (e.g. 10) to respect credits.

2. **Per row, mark in-flight.** `content.mark(client, id, content.GENERATING)`.

3. **Generate via Higgsfield connector.** Pick the model by `Asset Type`:
   - Image / Cover Art / Ad Creative → `image_auto` (or `flux_2` for precise
     prompt adherence).
   - Video / Social Clip → `veo3` or `grok_video` (image-to-video needs a start
     image; generate the still first if absent).
   Use the row's `Prompt` and `Brand`. Apply the matching HyperFrames skill /
   house style for the brand. Poll the job to completion; on failure,
   `content.mark(client, id, content.FAILED, note=<reason>)` and continue.

4. **Store + tag in Cloudinary.** Upload the output to the folder convention
   `brand/venture/asset-type/date` (e.g. `wrich-velvyt/teaser/video/2026-06-02`).
   Tag with brand + asset type.

5. **Record output.** `content.mark(client, id, content.GENERATED,
   output_url=<cloudinary url>, cloudinary_folder=<folder>)`.

6. **Queue for approval.** `approvals.submit_for_approval(client, item=<title>,
   type_=approvals.CONTENT, summary=<one line>, brand=<brand>,
   preview_link=<cloudinary url>, tier="B", source_table="Content Queue",
   source_record=<id>)`. The helper enforces Tier B and sets status
   "Needs Approval".

7. **Summarize the run** in the log: counts generated / failed / queued.

## Guardrails

- Tier B throughout. The routine **never** posts to social, Shopify, or anywhere
  public — it only produces drafts and files them in Needs Approval.
- Respect the credit budget: cap the nightly batch; on repeated generation
  failures, stop and report rather than burning credits.
- Pre-fill Content Queue rows yourself (prompt + brand + asset type); the routine
  does not invent briefs.
