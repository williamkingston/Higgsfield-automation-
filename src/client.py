"""Single entry point for all Higgsfield API calls.

Per CLAUDE.md conventions: every request goes through HiggsfieldClient so
retry/backoff and request-id logging stay in one place instead of being
re-implemented at every call site.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any

import requests

logger = logging.getLogger("higgsfield.client")

DEFAULT_API_BASE = "https://api.higgsfield.ai"
MAX_RETRIES = 5
INITIAL_BACKOFF_SECONDS = 1.0


class HiggsfieldAPIError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None, request_id: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.request_id = request_id


@dataclass
class Job:
    id: str
    status: str
    raw: dict[str, Any]

    @property
    def is_terminal(self) -> bool:
        return self.status in ("completed", "failed")


class HiggsfieldClient:
    """Thin wrapper around the Higgsfield REST API.

    Requires HIGGSFIELD_API_KEY to be set (directly or via a loaded .env).
    """

    def __init__(self, api_key: str | None = None, api_base: str | None = None, session: requests.Session | None = None):
        self.api_key = api_key or os.environ.get("HIGGSFIELD_API_KEY")
        if not self.api_key:
            raise HiggsfieldAPIError("HIGGSFIELD_API_KEY is not set")
        self.api_base = (api_base or os.environ.get("HIGGSFIELD_API_BASE") or DEFAULT_API_BASE).rstrip("/")
        self.session = session or requests.Session()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        url = f"{self.api_base}{path}"
        backoff = INITIAL_BACKOFF_SECONDS
        for attempt in range(1, MAX_RETRIES + 1):
            response = self.session.request(method, url, headers=self._headers(), timeout=60, **kwargs)
            request_id = response.headers.get("x-request-id")
            if response.status_code == 429 and attempt < MAX_RETRIES:
                logger.warning("Rate limited (request_id=%s), retrying in %.1fs", request_id, backoff)
                time.sleep(backoff)
                backoff *= 2
                continue
            if not response.ok:
                raise HiggsfieldAPIError(
                    f"{method} {path} failed with {response.status_code}",
                    status_code=response.status_code,
                    request_id=request_id,
                )
            logger.info("%s %s succeeded (request_id=%s)", method, path, request_id)
            return response.json()
        raise HiggsfieldAPIError(f"{method} {path} failed after {MAX_RETRIES} retries")

    def generate_video(self, prompt: str, references: list[str] | None = None, **params: Any) -> Job:
        """Submit an async video generation job. Returns the created Job (queued/processing)."""
        body: dict[str, Any] = {"prompt": prompt, **params}
        if references:
            body["reference_image_urls"] = references
        data = self._request("POST", "/v1/videos", json=body)
        return Job(id=data["id"], status=data["status"], raw=data)

    def get_job(self, job_id: str) -> Job:
        data = self._request("GET", f"/v1/jobs/{job_id}")
        return Job(id=data["id"], status=data["status"], raw=data)

    def wait_for_job(self, job_id: str, poll_interval_seconds: float = 5.0, timeout_seconds: float = 1800.0) -> Job:
        """Poll job status until it is completed or failed, or timeout is reached."""
        deadline = time.monotonic() + timeout_seconds
        while True:
            job = self.get_job(job_id)
            if job.is_terminal:
                return job
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timed out waiting for job {job_id} (last status: {job.status})")
            time.sleep(poll_interval_seconds)
