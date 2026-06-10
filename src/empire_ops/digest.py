"""Compose and store the morning money/sales digest (plan §5, Phase 3B / 4).

This is reporting only — Tier A by action (writing a summary), reading Tier C
data (money/credit). It aggregates read-only readings from the source connectors
into a plain-English summary, a cash figure, and a flags block, then writes one
row to the Money Digest Log. It never moves money, touches credit, or acts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as date_cls
from datetime import datetime, timezone

from .airtable import AirtableClient
from .schema import MoneyDigestLog

DIGEST_TIER = "C (read-only)"


@dataclass
class MetricReading:
    """One read-only number pulled from a source connector."""

    source: str          # e.g. "Shopify", "QuickBooks", "Square"
    label: str           # e.g. "Sales (yesterday)", "Operating balance"
    value: str           # pre-formatted display value, e.g. "$1,240.00"
    flag: str | None = None  # set when this reading should raise an alert


@dataclass
class Digest:
    digest_date: date_cls
    readings: list[MetricReading] = field(default_factory=list)
    cash_position: float | None = None

    @property
    def sources(self) -> list[str]:
        seen: list[str] = []
        for r in self.readings:
            if r.source not in seen:
                seen.append(r.source)
        return seen

    @property
    def flags(self) -> list[str]:
        return [f"{r.source} — {r.flag}" for r in self.readings if r.flag]

    def summary(self) -> str:
        """Plain-English digest body, grouped by source."""
        if not self.readings:
            return "No readings available for this period."
        lines: list[str] = []
        for source in self.sources:
            lines.append(f"{source}:")
            for r in self.readings:
                if r.source == source:
                    mark = "  ⚠ " if r.flag else "  • "
                    lines.append(f"{mark}{r.label}: {r.value}")
        if self.flags:
            lines.append("")
            lines.append(f"Flags: {len(self.flags)}")
        return "\n".join(lines)

    def to_fields(self) -> dict[str, object]:
        fields: dict[str, object] = {
            MoneyDigestLog.DIGEST_DATE: self.digest_date.isoformat(),
            MoneyDigestLog.SUMMARY: self.summary(),
            MoneyDigestLog.SOURCES: ", ".join(self.sources) or "—",
            MoneyDigestLog.FLAGS: "\n".join(self.flags) or "None",
            MoneyDigestLog.TIER: DIGEST_TIER,
            MoneyDigestLog.GENERATED_AT: datetime.now(timezone.utc).isoformat(),
        }
        if self.cash_position is not None:
            fields[MoneyDigestLog.CASH_POSITION] = self.cash_position
        return fields


def write_digest(client: AirtableClient, digest: Digest) -> dict:
    """Write the digest to the Money Digest Log and return the created record."""
    created = client.create_records(MoneyDigestLog.TABLE_ID, [digest.to_fields()])
    return created[0]
