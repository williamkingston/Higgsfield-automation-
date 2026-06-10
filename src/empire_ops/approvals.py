"""Push Tier-B drafts into the Needs Approval queue.

Phases 1, 2, 3A, and 5 all end the same way: a finished draft lands in Needs
Approval with a preview, and a human approves before anything publishes. This is
the single chokepoint for that, so the guardrail check lives here — callers can't
forget it.
"""

from __future__ import annotations

from datetime import datetime, timezone

from . import guardrails
from .airtable import AirtableClient
from .schema import NeedsApproval

# Approval-queue item types (match the Needs Approval "Type" field choices).
CONTENT = "Content"
MUSIC = "Music"
LISTING = "Listing"
LEAD_RESPONSE = "Lead Response"
MONEY_ALERT = "Money Alert"
OTHER = "Other"


def submit_for_approval(
    client: AirtableClient,
    *,
    item: str,
    type_: str,
    summary: str,
    brand: str | None = None,
    preview_link: str | None = None,
    tier: str = "B",
    source_table: str | None = None,
    source_record: str | None = None,
) -> dict:
    """Create a Needs Approval row for a finished draft.

    Enforces the guardrail tier first: Tier C work must never reach this queue as
    an actionable item (it is read-and-alert only), so a Tier-C submission raises.
    """
    decision = guardrails.enforce(tier, f"queue {type_!r} for approval")

    fields: dict[str, object] = {
        NeedsApproval.ITEM: item,
        NeedsApproval.TYPE: type_,
        NeedsApproval.SUMMARY: summary,
        NeedsApproval.GUARDRAIL_TIER: decision.tier,
        NeedsApproval.APPROVAL_STATUS: "Needs Approval",
        NeedsApproval.SUBMITTED: datetime.now(timezone.utc).isoformat(),
    }
    if brand:
        fields[NeedsApproval.BRAND] = brand
    if preview_link:
        fields[NeedsApproval.PREVIEW_LINK] = preview_link
    if source_table:
        fields[NeedsApproval.SOURCE_TABLE] = source_table
    if source_record:
        fields[NeedsApproval.SOURCE_RECORD] = source_record

    created = client.create_records(NeedsApproval.TABLE_ID, [fields])
    return created[0]
