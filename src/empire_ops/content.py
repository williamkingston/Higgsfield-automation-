"""Content Queue helpers for the Phase 1 nightly content engine.

Deterministic, testable glue around the queue: pick the rows that are due, and
move a row through its lifecycle. The actual generation (Higgsfield) and storage
(Cloudinary) are done by the routine via the connectors.
"""

from __future__ import annotations

from datetime import date as date_cls

from .airtable import AirtableClient
from .schema import ContentQueue

# Content Queue status values (match the "Status" field choices).
QUEUED = "Queued"
GENERATING = "Generating"
GENERATED = "Generated"
FAILED = "Failed"


def _is_due(scheduled_for: str | None, today: date_cls) -> bool:
    """A row is due if it has no schedule or its date is today or earlier."""
    if not scheduled_for:
        return True
    try:
        return date_cls.fromisoformat(scheduled_for[:10]) <= today
    except ValueError:
        return True


def ready_rows(client: AirtableClient, *, today: date_cls | None = None) -> list[dict]:
    """Return Content Queue rows that are Queued and due to generate now."""
    today = today or date_cls.today()
    rows: list[dict] = []
    for record in client.list_records(ContentQueue.TABLE_ID):
        fields = record["fields"]
        if fields.get(ContentQueue.STATUS) != QUEUED:
            continue
        if not _is_due(fields.get(ContentQueue.SCHEDULED_FOR), today):
            continue
        rows.append(record)
    return rows


def mark(
    client: AirtableClient,
    record_id: str,
    status: str,
    *,
    output_url: str | None = None,
    cloudinary_folder: str | None = None,
    note: str | None = None,
) -> dict:
    """Advance a Content Queue row's status, optionally recording output."""
    fields: dict[str, object] = {ContentQueue.STATUS: status}
    if output_url:
        fields[ContentQueue.OUTPUT_URL] = output_url
    if cloudinary_folder:
        fields[ContentQueue.CLOUDINARY_FOLDER] = cloudinary_folder
    if note:
        fields[ContentQueue.NOTES] = note
    return client.update_record(ContentQueue.TABLE_ID, record_id, fields)
