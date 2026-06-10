"""Shared test doubles."""

from __future__ import annotations

import itertools


class FakeAirtable:
    """In-memory stand-in for AirtableClient — records calls, hits no network."""

    def __init__(self, rows: list[dict] | None = None):
        self._rows = rows or []
        self.created: list[tuple[str, list[dict]]] = []
        self.updated: list[tuple[str, str, dict]] = []
        self._ids = (f"rec{n:014d}" for n in itertools.count(1))

    def list_records(self, table_id, **kwargs):
        yield from self._rows

    def create_records(self, table_id, records):
        self.created.append((table_id, records))
        return [{"id": next(self._ids), "fields": r} for r in records]

    def update_record(self, table_id, record_id, fields):
        self.updated.append((table_id, record_id, fields))
        return {"id": record_id, "fields": fields}
