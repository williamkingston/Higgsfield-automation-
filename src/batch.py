"""Resumable batch runner for Higgsfield generation jobs.

Submits a list of jobs, persists their generation ids to a JSON state file,
and resumes cleanly after a restart: already-completed jobs are skipped, and
in-flight jobs are recovered by id instead of re-submitted (see CLAUDE.md —
"store job IDs persistently so jobs can be recovered after a process restart").
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.client import (
    _FAILURE_STATES,
    _SUCCESS_STATES,
    HiggsfieldAPIError,
    HiggsfieldClient,
)

logger = logging.getLogger("higgsfield.batch")


@dataclass
class JobState:
    """Persisted state for a single job, keyed by a stable `key`."""

    key: str
    prompt: str
    output: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    generation_id: str | None = None
    status: str = "pending"  # pending | submitted | completed | failed
    output_url: str | None = None
    error: str | None = None

    @property
    def is_terminal(self) -> bool:
        return self.status in ("completed", "failed")


class BatchRunner:
    """Submit and track a batch of generation jobs with a JSON state file."""

    def __init__(self, client: HiggsfieldClient, state_path: str | Path) -> None:
        self.client = client
        self.state_path = Path(state_path)
        self.states: dict[str, JobState] = self._load()

    # -- persistence -------------------------------------------------------

    def _load(self) -> dict[str, JobState]:
        if not self.state_path.exists():
            return {}
        raw = json.loads(self.state_path.read_text())
        return {k: JobState(**v) for k, v in raw.items()}

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {k: asdict(v) for k, v in self.states.items()}
        # Write atomically so a crash mid-write can't corrupt the state file.
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        tmp.replace(self.state_path)

    # -- lifecycle ---------------------------------------------------------

    def _ensure_states(self, jobs: list[dict[str, Any]]) -> None:
        for job in jobs:
            key = job.get("key") or job["prompt"]
            if key in self.states:
                continue
            self.states[key] = JobState(
                key=key,
                prompt=job["prompt"],
                output=job.get("output"),
                params=job.get("params", {}),
            )
        self._save()

    def submit_pending(self) -> None:
        """Submit any job that hasn't been submitted yet, saving after each."""
        for state in self.states.values():
            if state.status != "pending" or state.generation_id:
                continue
            try:
                state.generation_id = self.client.submit_generation(state.prompt, **state.params)
                state.status = "submitted"
            except HiggsfieldAPIError as exc:
                state.status = "failed"
                state.error = str(exc)
                logger.error("Submit failed for %s: %s", state.key, exc)
            self._save()

    def poll_once(self) -> None:
        """Advance every in-flight job by one status check; download completions."""
        for state in self.states.values():
            if state.status != "submitted" or not state.generation_id:
                continue
            try:
                data = self.client.get_generation(state.generation_id)
            except HiggsfieldAPIError as exc:
                logger.warning("Poll error for %s: %s", state.key, exc)
                continue

            status = str(data.get("status", "unknown")).lower()
            if status in _SUCCESS_STATES:
                state.status = "completed"
                state.output_url = data.get("output_url") or data.get("url")
                if state.output and state.output_url:
                    self.client.download(state.output_url, state.output)
            elif status in _FAILURE_STATES:
                state.status = "failed"
                state.error = str(data.get("error", status))
            self._save()

    def run(
        self,
        jobs: list[dict[str, Any]],
        *,
        poll_interval: float = 5.0,
        timeout: float = 1800.0,
    ) -> dict[str, JobState]:
        """Submit `jobs` and poll until all are terminal or the deadline passes.

        Safe to call repeatedly with the same jobs — already-tracked jobs are
        not re-submitted.
        """
        self._ensure_states(jobs)
        self.submit_pending()

        deadline = time.monotonic() + timeout
        while any(s.status == "submitted" for s in self.states.values()):
            if time.monotonic() >= deadline:
                logger.warning("Batch timed out with %d job(s) still in flight", self.pending_count)
                break
            self.poll_once()
            if any(s.status == "submitted" for s in self.states.values()):
                time.sleep(poll_interval)
        return self.states

    # -- reporting ---------------------------------------------------------

    @property
    def pending_count(self) -> int:
        return sum(1 for s in self.states.values() if s.status == "submitted")

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for s in self.states.values():
            counts[s.status] = counts.get(s.status, 0) + 1
        return counts
