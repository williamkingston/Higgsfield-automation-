import pytest

from src.empire_ops import approvals, guardrails
from src.empire_ops.schema import NeedsApproval
from tests.conftest import FakeAirtable


def test_tier_b_creates_needs_approval_row():
    client = FakeAirtable()
    approvals.submit_for_approval(
        client,
        item="Wr!ch Velvyt teaser",
        type_=approvals.CONTENT,
        summary="30s teaser generated, awaiting review.",
        brand="Wr!ch Velvyt",
        preview_link="https://res.cloudinary.com/demo/x.mp4",
        tier="B",
        source_table="Content Queue",
        source_record="recABC",
    )
    assert len(client.created) == 1
    table_id, records = client.created[0]
    assert table_id == NeedsApproval.TABLE_ID
    fields = records[0]
    assert fields[NeedsApproval.APPROVAL_STATUS] == "Needs Approval"
    assert fields[NeedsApproval.GUARDRAIL_TIER] == "B"
    assert fields[NeedsApproval.PREVIEW_LINK].startswith("https://")


def test_tier_c_submission_is_blocked():
    client = FakeAirtable()
    with pytest.raises(guardrails.GuardrailViolation):
        approvals.submit_for_approval(
            client,
            item="Stripe payout",
            type_=approvals.MONEY_ALERT,
            summary="never",
            tier="C",
        )
    assert client.created == []
