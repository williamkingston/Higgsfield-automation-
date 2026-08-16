"""JSON-backed persistence for Higgsfield job records.

Job IDs are stored on disk so a batch run can be recovered after a
process restart, per CLAUDE.md's "Working with the Higgsfield API"
guidance.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

TERMINAL_STATUSES = ("completed", "failed")


class JobStore:
    def __init__(self, path: str | os.PathLike) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}")

    def _read(self) -> dict[str, Any]:
        return json.loads(self.path.read_text())

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True))

    def upsert(self, job_id: str, record: dict[str, Any]) -> None:
        data = self._read()
        data[job_id] = record
        self._write(data)

    def all(self) -> dict[str, Any]:
        return self._read()

    def pending(self) -> dict[str, Any]:
        return {job_id: record for job_id, record in self._read().items() if record.get("status") not in TERMINAL_STATUSES}
