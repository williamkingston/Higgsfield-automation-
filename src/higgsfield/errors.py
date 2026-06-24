"""Exception types raised by the Higgsfield client.

Every error carries enough context (status code, request id) to be actionable
without leaking the API key or full response bodies.
"""

from __future__ import annotations


class HiggsfieldError(Exception):
    """Base class for all errors raised by this package."""


class ConfigError(HiggsfieldError):
    """Raised when required configuration is missing or invalid."""


class APIError(HiggsfieldError):
    """Raised when the Higgsfield API returns an unsuccessful response.

    Attributes:
        status_code: HTTP status code returned by the API.
        request_id: The API request id, when present, for traceability.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        request_id: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.request_id = request_id
        if request_id:
            message = f"{message} (request_id={request_id})"
        super().__init__(message)


class RateLimitError(APIError):
    """Raised when the API responds with 429 after retries are exhausted."""


class JobError(HiggsfieldError):
    """Raised when an asynchronous generation job ends in a failed state."""

    def __init__(self, message: str, *, job_id: str | None = None) -> None:
        self.job_id = job_id
        if job_id:
            message = f"{message} (job_id={job_id})"
        super().__init__(message)


class JobTimeout(JobError):
    """Raised when a job does not reach a terminal state within the deadline."""
