"""Guardrail enforcement (plan §4).

Every routine calls :func:`check` before it acts. Tier A passes through, Tier B
is routed to the Needs Approval queue, and Tier C aborts hard — a routine can
read and alert on money/credit/legal, but it can never act.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from . import config

_POLICY_PATH = config.REPO_ROOT / "config" / "guardrails.yaml"


class GuardrailViolation(RuntimeError):
    """Raised when a routine attempts an action its tier forbids."""


@dataclass(frozen=True)
class Decision:
    tier: str
    may_act: bool
    requires_approval: bool
    reason: str


@lru_cache(maxsize=1)
def policy(path: Path | None = None) -> dict:
    """Load and cache the guardrail policy."""
    with open(path or _POLICY_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def tier_for_connector(connector: str) -> str:
    """Return the default tier for a connector, defaulting to the strictest (C)."""
    return policy()["connector_default_tier"].get(connector, "C")


def check(tier: str) -> Decision:
    """Resolve what a routine may do at ``tier``.

    Tier A → act. Tier B → act, then require approval. Tier C → no action.
    """
    tier = (tier or "").strip().upper()
    tiers = policy()["tiers"]
    if tier not in tiers:
        raise GuardrailViolation(
            f"Unknown guardrail tier {tier!r}; expected one of {sorted(tiers)}."
        )
    spec = tiers[tier]
    return Decision(
        tier=tier,
        may_act=bool(spec.get("may_act", False)),
        requires_approval=bool(spec.get("requires_approval", False)),
        reason=spec.get("description", "").strip(),
    )


def enforce(tier: str, action: str = "this action") -> Decision:
    """Like :func:`check`, but raises on Tier C so callers can guard a code path.

    Use for irreversible/outward steps. Tier-C work (money, credit, legal) must
    go through a human — the routine only reads and alerts.
    """
    decision = check(tier)
    if not decision.may_act:
        raise GuardrailViolation(
            f"Tier {decision.tier} forbids automated action: {action}. "
            f"Routines may read and alert only. {decision.reason}"
        )
    return decision
