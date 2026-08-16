"""Single entry point for all Higgsfield API calls.

Per CLAUDE.md convention, every request to the Higgsfield API must go
through this module — never scatter raw `requests` calls elsewhere in
the codebase.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

DEFAULT_API_BASE = "https://api.higgsfield.ai"
DEFAULT_TIMEOUT_SECONDS = 30
MAX_RETRIES = 5
BACKOFF_BASE_SECONDS = 1.0


class HiggsfieldAPIError(RuntimeError):
    """Raised for non-retryable Higgsfield API failures."""


class HiggsfieldClient:
    """Thin wrapper around the Higgsfield HTTP API.

    Higgsfield's unlimited-generations tier removes the account-level quota,
    but the API still enforces per-request rate limits, so 429s are retried
    with exponential backoff rather than treated as fatal.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
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

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.api_base}{path}"
        for attempt in range(1, MAX_RETRIES + 1):
            response = self.session.request(
                method, url, headers=self._headers(), timeout=DEFAULT_TIMEOUT_SECONDS, **kwargs
            )
            request_id = response.headers.get("x-request-id")

            if response.status_code == 429:
                if attempt == MAX_RETRIES:
                    raise HiggsfieldAPIError(
                        f"Rate limited after {MAX_RETRIES} attempts (request_id={request_id})"
                    )
                retry_after = float(response.headers.get("Retry-After", 0)) or BACKOFF_BASE_SECONDS * (
                    2 ** (attempt - 1)
                )
                logger.warning(
                    "Higgsfield API rate limited (request_id=%s); retrying in %.1fs", request_id, retry_after
                )
                time.sleep(retry_after)
                continue

            if response.status_code >= 500:
                if attempt == MAX_RETRIES:
                    response.raise_for_status()
                backoff = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    "Higgsfield API server error %s (request_id=%s); retrying in %.1fs",
                    response.status_code,
                    request_id,
                    backoff,
                )
                time.sleep(backoff)
                continue

            if not response.ok:
                raise HiggsfieldAPIError(
                    f"Higgsfield API error {response.status_code} (request_id={request_id}): {response.text[:500]}"
                )

            logger.info("Higgsfield API %s %s -> %s (request_id=%s)", method, path, response.status_code, request_id)
            return response.json() if response.content else {}

        raise HiggsfieldAPIError("unreachable")  # pragma: no cover

    def create_video_generation(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Submit an async video generation job. Returns a dict containing `job_id`."""
        return self._request("POST", "/v1/videos/generations", json=payload)

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Fetch job status. `status` is one of the API's async job states
        (e.g. queued/processing/completed/failed) — always check it before
        touching `output`."""
        return self._request("GET", f"/v1/jobs/{job_id}")

    def download_asset(self, url: str, dest_path: str) -> str:
        response = self.session.get(url, timeout=DEFAULT_TIMEOUT_SECONDS)
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(response.content)
        return dest_path
