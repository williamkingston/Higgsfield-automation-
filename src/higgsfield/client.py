"""Single entry point for all Higgsfield API calls.

Per the repository conventions, every request to Higgsfield goes through this
module — there are no scattered ``requests`` calls elsewhere. The client adds
bearer authentication, exponential backoff on rate limits and transient server
errors, request-id logging for traceability, and the submit-then-poll pattern
for asynchronous generation jobs.
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

import requests

from .config import HiggsfieldConfig
from .errors import APIError, JobError, JobTimeout, RateLimitError

logger = logging.getLogger("higgsfield")

# Endpoint paths are centralized so they can be matched to the real API surface
# without touching call sites.
GENERATIONS_PATH = "/v1/generations"
JOB_PATH = "/v1/jobs/{job_id}"

# Job lifecycle states.
TERMINAL_SUCCESS = {"completed", "succeeded", "success"}
TERMINAL_FAILURE = {"failed", "error", "cancelled", "canceled"}

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class Job:
    """A snapshot of an asynchronous generation job.

    ``raw`` retains the full decoded response so callers can read fields that
    are not promoted to first-class attributes here.
    """

    id: str
    status: str
    raw: Mapping[str, Any]

    @property
    def is_complete(self) -> bool:
        return self.status.lower() in TERMINAL_SUCCESS

    @property
    def is_failed(self) -> bool:
        return self.status.lower() in TERMINAL_FAILURE

    @property
    def is_terminal(self) -> bool:
        return self.is_complete or self.is_failed

    @property
    def output_url(self) -> str | None:
        """Best-effort extraction of the primary output asset URL."""
        for key in ("output_url", "result_url", "url"):
            value = self.raw.get(key)
            if isinstance(value, str) and value:
                return value
        result = self.raw.get("result")
        if isinstance(result, Mapping):
            for key in ("url", "output_url"):
                value = result.get(key)
                if isinstance(value, str) and value:
                    return value
        return None


class HiggsfieldClient:
    """HTTP client for the Higgsfield video-generation API."""

    def __init__(
        self,
        config: HiggsfieldConfig | None = None,
        *,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config or HiggsfieldConfig.from_env()
        self._session = session or requests.Session()
        # Injectable so tests don't actually sleep through backoff.
        self._sleep = sleep

    # -- public API -----------------------------------------------------------

    def create_generation(self, payload: Mapping[str, Any]) -> Job:
        """Submit a generation job and return its initial :class:`Job` state."""
        data = self._request("POST", GENERATIONS_PATH, json=payload)
        return self._job_from_response(data)

    def get_job(self, job_id: str) -> Job:
        """Fetch the current state of a job by id."""
        if not job_id:
            raise ValueError("job_id must be a non-empty string")
        data = self._request("GET", JOB_PATH.format(job_id=job_id))
        return self._job_from_response(data, fallback_id=job_id)

    def wait_for_job(
        self,
        job_id: str,
        *,
        poll_interval: float = 5.0,
        timeout: float = 600.0,
    ) -> Job:
        """Poll a job until it reaches a terminal state.

        Returns the completed :class:`Job`. Raises :class:`JobError` if the job
        fails and :class:`JobTimeout` if it does not finish within ``timeout``
        seconds.
        """
        deadline = time.monotonic() + timeout
        while True:
            job = self.get_job(job_id)
            if job.is_complete:
                logger.info("Job %s completed", job.id)
                return job
            if job.is_failed:
                raise JobError(
                    f"Job ended in non-success state {job.status!r}", job_id=job.id
                )
            if time.monotonic() >= deadline:
                raise JobTimeout(
                    f"Job did not finish within {timeout:.0f}s "
                    f"(last status {job.status!r})",
                    job_id=job.id,
                )
            self._sleep(poll_interval)

    def generate_and_wait(
        self,
        payload: Mapping[str, Any],
        *,
        poll_interval: float = 5.0,
        timeout: float = 600.0,
    ) -> Job:
        """Convenience: submit a job and block until it is complete."""
        job = self.create_generation(payload)
        return self.wait_for_job(
            job.id, poll_interval=poll_interval, timeout=timeout
        )

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> HiggsfieldClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- internals ------------------------------------------------------------

    def _auth_headers(self) -> dict[str, str]:
        # Authentication is isolated here: a one-line change if the scheme ever
        # differs from bearer tokens.
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Accept": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        url = f"{self.config.api_base}{path}"
        headers = self._auth_headers()

        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            response = self._session.request(
                method,
                url,
                json=json,
                headers=headers,
                timeout=self.config.timeout,
            )
            request_id = _request_id(response)
            logger.debug(
                "%s %s -> %s (request_id=%s)",
                method,
                path,
                response.status_code,
                request_id or "n/a",
            )

            if response.status_code in _RETRYABLE_STATUS:
                last_error = self._error_for(response, request_id)
                if attempt < self.config.max_retries:
                    delay = self._backoff_delay(attempt, response)
                    logger.warning(
                        "Retryable status %s on %s; retrying in %.2fs "
                        "(attempt %d/%d, request_id=%s)",
                        response.status_code,
                        path,
                        delay,
                        attempt + 1,
                        self.config.max_retries,
                        request_id or "n/a",
                    )
                    self._sleep(delay)
                    continue
                raise last_error

            if not response.ok:
                raise self._error_for(response, request_id)

            return _decode_json(response, request_id)

        # Loop always returns or raises; this satisfies type checkers.
        raise last_error or APIError("Request failed without a response")

    def _backoff_delay(self, attempt: int, response: requests.Response) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass
        # Exponential backoff with full jitter.
        return random.uniform(0.0, min(60.0, 2.0**attempt))

    def _error_for(
        self, response: requests.Response, request_id: str | None
    ) -> APIError:
        # Deliberately does not include the response body, which may contain PII.
        message = f"Higgsfield API returned {response.status_code}"
        if response.status_code == 429:
            return RateLimitError(
                message, status_code=429, request_id=request_id
            )
        return APIError(
            message, status_code=response.status_code, request_id=request_id
        )

    @staticmethod
    def _job_from_response(
        data: Mapping[str, Any], *, fallback_id: str | None = None
    ) -> Job:
        job_id = data.get("id") or data.get("job_id") or fallback_id
        if not job_id:
            raise APIError("API response did not include a job id")
        status = str(data.get("status", "pending"))
        return Job(id=str(job_id), status=status, raw=data)


def _request_id(response: requests.Response) -> str | None:
    for header in ("x-request-id", "x-higgsfield-request-id", "request-id"):
        value = response.headers.get(header)
        if value:
            return value
    return None


def _decode_json(
    response: requests.Response, request_id: str | None
) -> Mapping[str, Any]:
    try:
        body = response.json()
    except ValueError as exc:
        raise APIError(
            "API response was not valid JSON",
            status_code=response.status_code,
            request_id=request_id,
        ) from exc
    if not isinstance(body, Mapping):
        raise APIError(
            "API response was not a JSON object",
            status_code=response.status_code,
            request_id=request_id,
        )
    return body
