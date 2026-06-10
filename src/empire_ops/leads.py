"""Lead intake helpers for the Phase 5 lead loop (Ray's Elite Transport, YvesBnB).

A webhook drops a new lead in; the routine drafts a response into Needs Approval
and places a tentative calendar hold. Tier B — you send. Booking/confirmation
stays human.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .airtable import AirtableClient
from .schema import Leads

# Leads status values (match the "Status" field choices).
NEW = "New"
DRAFTED = "Drafted"
AWAITING_APPROVAL = "Awaiting Approval"
RESPONDED = "Responded"
WON = "Won"
LOST = "Lost"

# Sources that map directly to a brand in the approval queue.
_SOURCE_BRANDS = {"Ray's Elite Transport", "YvesBnB"}


def intake(
    client: AirtableClient,
    *,
    name: str,
    source: str,
    request: str,
    email: str | None = None,
    phone: str | None = None,
    received: str | None = None,
) -> dict:
    """Record a new lead. Returns the created record."""
    fields: dict[str, object] = {
        Leads.NAME: name,
        Leads.SOURCE: source,
        Leads.REQUEST: request,
        Leads.STATUS: NEW,
        Leads.RECEIVED: received or datetime.now(timezone.utc).isoformat(),
    }
    if email:
        fields[Leads.EMAIL] = email
    if phone:
        fields[Leads.PHONE] = phone
    return client.create_records(Leads.TABLE_ID, [fields])[0]


def new_leads(client: AirtableClient) -> list[dict]:
    """Return leads still in the 'New' state, awaiting a drafted response."""
    return [
        record
        for record in client.list_records(Leads.TABLE_ID)
        if record["fields"].get(Leads.STATUS) == NEW
    ]


def attach_draft(
    client: AirtableClient,
    record_id: str,
    draft_response: str,
    *,
    status: str = AWAITING_APPROVAL,
) -> dict:
    """Write a drafted reply onto the lead and advance its status."""
    return client.update_record(
        Leads.TABLE_ID,
        record_id,
        {Leads.DRAFT_RESPONSE: draft_response, Leads.STATUS: status},
    )


def brand_for_source(source: str) -> str | None:
    """Map a lead source to an approval-queue brand, if it is one."""
    return source if source in _SOURCE_BRANDS else None


def calendar_hold(
    *,
    name: str,
    source: str,
    request: str,
    start: str,
    end: str,
) -> dict:
    """Build a tentative calendar-hold event for the connector to create.

    The hold is a placeholder only — confirming the booking stays human (Tier B).
    """
    return {
        "summary": f"[HOLD] {source} — {name}",
        "description": f"Tentative hold pending approval.\n\nRequest:\n{request}",
        "start": start,
        "end": end,
        "transparency": "tentative",
    }
