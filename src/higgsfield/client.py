"""Higgsfield API client.

Every Higgsfield API call in this codebase goes through this module. Video
generation is asynchronous: `create_video_job` submits a job and returns its id,
then `wait_for_job` polls until the job reaches a terminal state.

Endpoint paths are defined as constants so they can be adjusted to match the
deployed API surface without touching call sites.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import requests

logger = logging.getLogger("higgsfield")

# Endpoint paths — adjust here if the API surface differs.
PATH_CREATE_VIDEO = "/v1/video/generate"
PATH_JOB_STATUS = "/v1/jobs/{job_id}"

TERMINAL_SUCCESS = "completed"
TERMINAL_FAILURE = "failed"

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class HiggsfieldError(RuntimeError):
    """Raised when the API returns an unrecoverable error."""


class JobFailedError(HiggsfieldError):
    """Raised when a generation job finishes in a failed state."""


@dataclass
class Job:
    id: str
    status: str
    output_url: str | None = None
    raw: dict[str, Any] | None = None

    @property
    def is_done(self) -> bool:
        return self.status in (TERMINAL_SUCCESS, TERMINAL_FAILURE)

    @property
    def succeeded(self) -> bool:
        return self.status == TERMINAL_SUCCESS


class HiggsfieldClient:
    def __init__(
        self,
        api_key: str,
        api_base: str,
        *,
        timeout: float = 30.0,
        max_retries: int = 5,
        session: requests.Session | None = None,
    ) -> None:
        self._api_base = api_base.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            }
        )

    def create_video_job(self, prompt: str, **params: Any) -> Job:
        """Submit a video generation job and return it in its initial state."""
        payload = {"prompt": prompt, **params}
        data = self._request("POST", PATH_CREATE_VIDEO, json=payload)
        return self._parse_job(data)

    def get_job(self, job_id: str) -> Job:
        data = self._request("GET", PATH_JOB_STATUS.format(job_id=job_id))
        return self._parse_job(data)

    def wait_for_job(
        self,
        job_id: str,
        *,
        poll_interval: float = 5.0,
        max_wait: float = 900.0,
    ) -> Job:
        """Poll a job until it succeeds, fails, or `max_wait` is exceeded."""
        deadline = time.monotonic() + max_wait
        while True:
            job = self.get_job(job_id)
            if job.is_done:
                if not job.succeeded:
                    raise JobFailedError(f"Job {job_id} finished with status '{job.status}'.")
                return job
            if time.monotonic() >= deadline:
                raise HiggsfieldError(f"Job {job_id} did not finish within {max_wait:.0f}s.")
            time.sleep(poll_interval)

    # --- internals -------------------------------------------------------

    def _parse_job(self, data: dict[str, Any]) -> Job:
        job_id = data.get("id") or data.get("job_id")
        if not job_id:
            raise HiggsfieldError(f"API response did not include a job id: {data!r}")
        return Job(
            id=str(job_id),
            status=str(data.get("status", "unknown")),
            output_url=data.get("output_url") or data.get("url"),
            raw=data,
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self._api_base}{path}"
        backoff = 1.0
        for attempt in range(1, self._max_retries + 1):
            response = self._session.request(method, url, timeout=self._timeout, **kwargs)
            request_id = response.headers.get("x-request-id", "-")

            if response.status_code in _RETRYABLE_STATUS and attempt < self._max_retries:
                wait = self._retry_after(response, backoff)
                logger.warning(
                    "%s %s -> %s (request_id=%s); retry %d/%d in %.1fs",
                    method, path, response.status_code, request_id,
                    attempt, self._max_retries, wait,
                )
                time.sleep(wait)
                backoff *= 2
                continue

            if not response.ok:
                raise HiggsfieldError(
                    f"{method} {path} failed: {response.status_code} "
                    f"(request_id={request_id})"
                )

            logger.info("%s %s -> %s (request_id=%s)", method, path, response.status_code, request_id)
            return response.json()

        raise HiggsfieldError(f"{method} {path} exhausted {self._max_retries} retries.")

    @staticmethod
    def _retry_after(response: requests.Response, fallback: float) -> float:
        header = response.headers.get("Retry-After")
        if header:
            try:
                return float(header)
            except ValueError:
                pass
        return fallback
