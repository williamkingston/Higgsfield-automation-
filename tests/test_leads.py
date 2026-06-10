from src.empire_ops import leads
from src.empire_ops.schema import Leads
from tests.conftest import FakeAirtable


def _row(rec_id, status):
    return {"id": rec_id, "fields": {Leads.STATUS: status}}


def test_intake_creates_new_lead_with_received_stamp():
    client = FakeAirtable()
    leads.intake(
        client,
        name="Jordan P.",
        source="Ray's Elite Transport",
        request="Airport pickup for 4, June 20, 6am.",
        email="jordan@example.com",
    )
    table_id, records = client.created[0]
    assert table_id == Leads.TABLE_ID
    fields = records[0]
    assert fields[Leads.STATUS] == leads.NEW
    assert fields[Leads.EMAIL] == "jordan@example.com"
    assert fields[Leads.RECEIVED]  # stamped


def test_new_leads_filters_by_status():
    client = FakeAirtable(
        [
            _row("rec1", leads.NEW),
            _row("rec2", leads.WON),
            _row("rec3", leads.NEW),
        ]
    )
    assert {r["id"] for r in leads.new_leads(client)} == {"rec1", "rec3"}


def test_attach_draft_advances_to_awaiting_approval():
    client = FakeAirtable()
    leads.attach_draft(client, "rec1", "Hi Jordan, happy to help…")
    _, record_id, fields = client.updated[0]
    assert record_id == "rec1"
    assert fields[Leads.STATUS] == leads.AWAITING_APPROVAL
    assert fields[Leads.DRAFT_RESPONSE].startswith("Hi Jordan")


def test_brand_for_source_maps_known_sources():
    assert leads.brand_for_source("Ray's Elite Transport") == "Ray's Elite Transport"
    assert leads.brand_for_source("YvesBnB") == "YvesBnB"
    assert leads.brand_for_source("Website") is None


def test_calendar_hold_is_tentative():
    hold = leads.calendar_hold(
        name="Jordan P.",
        source="Ray's Elite Transport",
        request="Airport pickup",
        start="2026-06-20T06:00:00-04:00",
        end="2026-06-20T07:00:00-04:00",
    )
    assert hold["summary"].startswith("[HOLD]")
    assert hold["transparency"] == "tentative"
