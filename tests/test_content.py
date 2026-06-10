from datetime import date

from src.empire_ops import content
from src.empire_ops.schema import ContentQueue
from tests.conftest import FakeAirtable


def _row(rec_id, status, scheduled=None):
    fields = {ContentQueue.STATUS: status}
    if scheduled:
        fields[ContentQueue.SCHEDULED_FOR] = scheduled
    return {"id": rec_id, "fields": fields}


def test_is_due():
    today = date(2026, 6, 2)
    assert content._is_due(None, today) is True
    assert content._is_due("2026-06-01", today) is True
    assert content._is_due("2026-06-02", today) is True
    assert content._is_due("2026-06-03", today) is False


def test_ready_rows_filters_status_and_due_date():
    today = date(2026, 6, 2)
    client = FakeAirtable(
        [
            _row("rec1", content.QUEUED),
            _row("rec2", content.GENERATED),          # wrong status
            _row("rec3", content.QUEUED, "2026-12-01"),  # not due yet
            _row("rec4", content.QUEUED, "2026-06-02"),  # due today
        ]
    )
    ready = content.ready_rows(client, today=today)
    assert {r["id"] for r in ready} == {"rec1", "rec4"}


def test_enqueue_creates_queued_row():
    client = FakeAirtable()
    content.enqueue(
        client,
        title="Wr!ch Velvyt teaser",
        prompt="luxury teaser, dark premium palette",
        brand="Wr!ch Velvyt",
        asset_type="Video",
    )
    table_id, records = client.created[0]
    assert table_id == ContentQueue.TABLE_ID
    assert records[0][ContentQueue.STATUS] == content.QUEUED
    assert records[0][ContentQueue.GUARDRAIL_TIER] == "B"


def test_mark_sets_status_and_output():
    client = FakeAirtable()
    content.mark(
        client, "rec1", content.GENERATED,
        output_url="https://res.cloudinary.com/demo/x.mp4",
        cloudinary_folder="wrich-velvyt/teaser/video/2026-06-02",
    )
    table_id, record_id, fields = client.updated[0]
    assert table_id == ContentQueue.TABLE_ID
    assert fields[ContentQueue.STATUS] == content.GENERATED
    assert fields[ContentQueue.OUTPUT_URL].endswith(".mp4")
