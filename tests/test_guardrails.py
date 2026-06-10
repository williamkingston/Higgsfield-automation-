"""Guardrail policy tests — the §4 rules are the non-negotiable core, so they
get the only Phase 0 tests."""

import pytest

from src.empire_ops import guardrails


def test_tier_a_acts_without_approval():
    d = guardrails.check("A")
    assert d.may_act is True
    assert d.requires_approval is False


def test_tier_b_acts_but_requires_approval():
    d = guardrails.check("B")
    assert d.may_act is True
    assert d.requires_approval is True


def test_tier_c_never_acts():
    d = guardrails.check("c")  # case-insensitive
    assert d.may_act is False
    assert d.requires_approval is False


def test_enforce_raises_on_tier_c():
    with pytest.raises(guardrails.GuardrailViolation):
        guardrails.enforce("C", "move money")


def test_enforce_allows_tier_b():
    assert guardrails.enforce("B", "draft a post").tier == "B"


def test_unknown_tier_raises():
    with pytest.raises(guardrails.GuardrailViolation):
        guardrails.check("Z")


def test_money_connectors_default_to_tier_c():
    for connector in ("stripe", "mercury", "brex", "ramp", "quickbooks"):
        assert guardrails.tier_for_connector(connector) == "C"


def test_unknown_connector_defaults_to_strictest():
    assert guardrails.tier_for_connector("some_new_bank") == "C"
