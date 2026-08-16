"""Batch video generation.

Higgsfield's unlimited-generations tier removes the per-account
generation cap, so this runner does not throttle how many jobs it
submits — it relies on HiggsfieldClient's retry/backoff to respect the
API's own per-request rate limit.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Iterable

from src.client import HiggsfieldClient
from src.storage import JobStore

logger = logging.getLogger(__name__)

DEFAULT_POLL_INTERVAL_SECONDS = 10.0


class BatchRunner:
    def __init__(self, client: HiggsfieldClient, job_store: JobStore, output_dir: str | Path) -> None:
        self.client = client
        self.job_store = job_store
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def submit_all(self, requests_: Iterable[dict[str, Any]]) -> list[str]:
        job_ids = []
        for payload in requests_:
            response = self.client.create_video_generation(payload)
            job_id = response["job_id"]
            self.job_store.upsert(job_id, {"status": "queued", "payload": payload})
            job_ids.append(job_id)
            logger.info("Submitted generation job %s", job_id)
        return job_ids

    def poll_until_complete(self, poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS) -> None:
        while self.job_store.pending():
            for job_id, record in self.job_store.pending().items():
                self._poll_one(job_id, record)
            if self.job_store.pending():
                time.sleep(poll_interval)

    def _poll_one(self, job_id: str, record: dict[str, Any]) -> None:
        status = self.client.get_job_status(job_id)
        record = {**record, "status": status["status"]}
        if status["status"] == "completed":
            asset_url = status["output"]["url"]
            dest = self.output_dir / f"{job_id}.mp4"
            self.client.download_asset(asset_url, str(dest))
            record["output_path"] = str(dest)
            logger.info("Job %s completed -> %s", job_id, dest)
        elif status["status"] == "failed":
            record["error"] = status.get("error")
            logger.error("Job %s failed: %s", job_id, record["error"])
        self.job_store.upsert(job_id, record)
