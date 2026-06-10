"""Phase 0 hello-world routine.

The plan's foundation check: a scheduled routine that reads one Airtable row and
writes back — confirming scheduling, auth, the guardrail tiers, and the single
Airtable client all work before any real loop is built.

It reads the oldest row in Content Queue, checks its guardrail tier, and stamps a
heartbeat into Notes. Tier C rows are read-only and never written.

Run:
    python -m routines.hello_world
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.empire_ops import guardrails
from src.empire_ops.airtable import AirtableClient
from src.empire_ops.schema import ContentQueue

log = logging.getLogger("empire_ops.routines.hello_world")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    client = AirtableClient()

    record = client.get_first(ContentQueue.TABLE_ID)
    if record is None:
        log.info("Content Queue is empty — nothing to read. Engine + auth OK.")
        return 0

    fields = record["fields"]
    title = fields.get(ContentQueue.TITLE, "(untitled)")
    tier = fields.get(ContentQueue.GUARDRAIL_TIER, "B")
    log.info("Read row %s (%s), tier %s", record["id"], title, tier)

    decision = guardrails.check(tier)
    if not decision.may_act:
        log.warning("Tier %s is read-only; not writing back to %s.", tier, title)
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    client.update_record(
        ContentQueue.TABLE_ID,
        record["id"],
        {ContentQueue.NOTES: f"✓ hello-world heartbeat {stamp}"},
    )
    log.info("Wrote heartbeat back to %s. Read/write loop confirmed.", title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
