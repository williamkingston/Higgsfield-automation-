"""Single entry point for all Lovart API calls.

Per the project conventions, every request to Lovart goes through this module
rather than scattering raw HTTP calls across the codebase. The client handles
authentication, retries with exponential backoff on rate limits, and the
asynchronous job-polling pattern Lovart uses for generation work.

Authentication
--------------
Lovart issues an access-key / secret-key pair (``ak_...`` / ``sk_...``). This
client sends both on every request via the ``X-Access-Key`` and ``X-Secret-Key``
headers. If your Lovart account uses a different scheme (for example an HMAC
request signature), override :meth:`LovartClient._auth_headers` — that method is
the single place auth is applied.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import requests

from .config import LovartConfig

logger = logging.getLogger("lovart")

# Endpoint paths. Adjust here if your Lovart API version differs.
GENERATE_PATH = "/v1/designs/generations"
JOB_STATUS_PATH = "/v1/designs/generations/{job_id}"

TERMINAL_STATUSES = {"completed", "succeeded", "failed", "canceled", "cancelled"}
SUCCESS_STATUSES = {"completed", "succeeded"}


class LovartError(Exception):
    """Base class for all Lovart client errors."""


class LovartAPIError(LovartError):
    """Raised when the API returns a non-success HTTP status.

    Carries the status code and the Lovart request id (when present) so
    failures are traceable without logging response bodies that may contain PII.
    """

    def __init__(self, message: str, status_code: int, request_id: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.request_id = request_id


@dataclass
class LovartJob:
    """A Lovart generation job and its current state."""

    id: str
    status: str
    raw: dict[str, Any]

    @property
    def is_terminal(self) -> bool:
        return self.status.lower() in TERMINAL_STATUSES

    @property
    def succeeded(self) -> bool:
        return self.status.lower() in SUCCESS_STATUSES


class LovartClient:
    """HTTP client for the Lovart API."""

    def __init__(
        self,
        config: LovartConfig | None = None,
        *,
        session: requests.Session | None = None,
        timeout: float = 30.0,
        max_retries: int = 4,
    ):
        self.config = config or LovartConfig.from_env()
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = session or requests.Session()

    # -- Authentication -------------------------------------------------

    def _auth_headers(self) -> dict[str, str]:
        """Return the headers that authenticate a request.

        Single source of truth for auth — change this method if Lovart's
        scheme differs. Never log the returned values; the secret key is
        sensitive.
        """
        return {
            "X-Access-Key": self.config.access_key,
            "X-Secret-Key": self.config.secret_key,
        }

    # -- Low-level request ----------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perform an authenticated request, retrying on 429 and 5xx.

        Returns the parsed JSON body. Raises :class:`LovartAPIError` on a
        non-success status after retries are exhausted.
        """
        url = f"{self.config.api_base}{path}"
        headers = {"Accept": "application/json", **self._auth_headers()}

        last_error: LovartAPIError | None = None
        for attempt in range(self.max_retries + 1):
            response = self._session.request(
                method,
                url,
                headers=headers,
                json=json,
                params=params,
                timeout=self.timeout,
            )
            request_id = response.headers.get("x-request-id")

            if response.status_code < 400:
                logger.debug("Lovart %s %s -> %s (request_id=%s)", method, path, response.status_code, request_id)
                if not response.content:
                    return {}
                return response.json()

            retryable = response.status_code == 429 or response.status_code >= 500
            last_error = LovartAPIError(
                f"Lovart API returned {response.status_code} for {method} {path}",
                status_code=response.status_code,
                request_id=request_id,
            )

            if retryable and attempt < self.max_retries:
                delay = self._retry_delay(response, attempt)
                logger.warning(
                    "Lovart %s %s -> %s, retrying in %.1fs (attempt %d/%d, request_id=%s)",
                    method, path, response.status_code, delay, attempt + 1, self.max_retries, request_id,
                )
                time.sleep(delay)
                continue

            raise last_error

        assert last_error is not None  # loop always sets it before exhausting
        raise last_error

    @staticmethod
    def _retry_delay(response: requests.Response, attempt: int) -> float:
        """Honour a ``Retry-After`` header when present, else exponential backoff."""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return 2.0 ** attempt

    # -- High-level operations ------------------------------------------

    def create_generation(self, prompt: str, **options: Any) -> LovartJob:
        """Submit a design/image generation job.

        ``options`` are passed through as additional request fields (for
        example ``aspect_ratio`` or ``style``); see the Lovart API docs for
        the fields your account supports.
        """
        payload: dict[str, Any] = {"prompt": prompt, **options}
        data = self.request("POST", GENERATE_PATH, json=payload)
        return self._job_from_response(data)

    def get_job(self, job_id: str) -> LovartJob:
        """Fetch the current state of a generation job."""
        data = self.request("GET", JOB_STATUS_PATH.format(job_id=job_id))
        return self._job_from_response(data)

    def wait_for_job(
        self,
        job_id: str,
        *,
        poll_interval: float = 3.0,
        timeout: float = 300.0,
    ) -> LovartJob:
        """Poll a job until it reaches a terminal state or ``timeout`` elapses."""
        deadline = time.monotonic() + timeout
        while True:
            job = self.get_job(job_id)
            if job.is_terminal:
                return job
            if time.monotonic() >= deadline:
                raise LovartError(
                    f"Timed out after {timeout:.0f}s waiting for Lovart job {job_id} "
                    f"(last status: {job.status})"
                )
            time.sleep(poll_interval)

    @staticmethod
    def _job_from_response(data: dict[str, Any]) -> LovartJob:
        job_id = data.get("id") or data.get("job_id") or ""
        status = data.get("status") or "unknown"
        if not job_id:
            raise LovartError("Lovart response did not include a job id")
        return LovartJob(id=str(job_id), status=str(status), raw=data)
