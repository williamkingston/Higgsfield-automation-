from datetime import date

from src.empire_ops import digest
from src.empire_ops.schema import MoneyDigestLog
from tests.conftest import FakeAirtable


def _sample() -> digest.Digest:
    return digest.Digest(
        digest_date=date(2026, 6, 2),
        cash_position=12_450.75,
        readings=[
            digest.MetricReading("Shopify", "Sales (yesterday)", "$1,240.00"),
            digest.MetricReading("QuickBooks", "Operating balance", "$11,210.75"),
            digest.MetricReading(
                "Ramp", "Card utilization", "82%", flag="utilization over 80%"
            ),
        ],
    )


def test_sources_are_deduped_and_ordered():
    assert _sample().sources == ["Shopify", "QuickBooks", "Ramp"]


def test_flags_collect_only_flagged_readings():
    flags = _sample().flags
    assert flags == ["Ramp — utilization over 80%"]


def test_summary_groups_by_source_and_marks_flags():
    text = _sample().summary()
    assert "Shopify:" in text
    assert "• Sales (yesterday): $1,240.00" in text
    assert "⚠ Card utilization: 82%" in text


def test_to_fields_pins_tier_c_and_sets_cash():
    fields = _sample().to_fields()
    assert fields[MoneyDigestLog.TIER] == digest.DIGEST_TIER
    assert fields[MoneyDigestLog.CASH_POSITION] == 12_450.75
    assert fields[MoneyDigestLog.DIGEST_DATE] == "2026-06-02"


def test_empty_digest_has_safe_summary_and_no_cash_field():
    d = digest.Digest(digest_date=date(2026, 6, 2))
    fields = d.to_fields()
    assert fields[MoneyDigestLog.FLAGS] == "None"
    assert MoneyDigestLog.CASH_POSITION not in fields
    assert "No readings" in fields[MoneyDigestLog.SUMMARY]


def test_write_digest_creates_one_row():
    client = FakeAirtable()
    digest.write_digest(client, _sample())
    assert len(client.created) == 1
    assert client.created[0][0] == MoneyDigestLog.TABLE_ID
