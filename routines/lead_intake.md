# Routine — Lead Intake (Phase 5)

**Trigger:** webhook (new lead form / email) — or a frequent cron sweep of new
leads. Counts against the 2–3 webhook-triggered runs/day.
**Guardrail:** Tier B — draft a response and place a tentative hold. **You send;
you confirm the booking.** Booking platforms stay manual.
**Tools:** Claude Code + the Leads table + Google Calendar connector + the
`empire_ops` helpers.

A scheduled/triggered Claude session runs these steps.

## Steps

1. **Record the lead.** From the webhook payload, `leads.intake(client,
   name=…, source=…, request=…, email=…, phone=…)`. (If leads arrive by another
   channel, sweep `leads.new_leads(client)` instead.)

2. **Draft a response.** Write a brief, on-brand reply to the request. Keep it
   specific to what they asked. Then `leads.attach_draft(client, id, draft)` —
   advances the lead to `Awaiting Approval`.

3. **Place a tentative calendar hold.** Build the event with
   `leads.calendar_hold(name=…, source=…, request=…, start=…, end=…)` and create
   it via the Calendar connector. The hold is a placeholder — it does not confirm
   anything.

4. **Queue for approval.** `approvals.submit_for_approval(client, item=<name>,
   type_=approvals.LEAD_RESPONSE, summary=<one line>,
   brand=leads.brand_for_source(source), tier="B", source_table="Leads",
   source_record=id)`.

5. **Summarize:** leads taken in, drafts queued, holds placed.

## Guardrails

- Tier B. The routine drafts and holds; it never sends the reply or confirms the
  booking — you do, from Needs Approval.
- Never auto-accept a booking, take payment, or commit a time. Holds are
  tentative only.
- Don't log full contact details beyond what the Leads row needs.
