"""Higgsfield Cloud API client.

Single entry point for all Higgsfield API calls (see CLAUDE.md). Handles
authentication, exponential backoff on rate limits, and the asynchronous
submit -> poll -> download lifecycle for video generation jobs.

Adapted from the OpenMontage `higgsfield_video` tool
(https://github.com/calesthio/OpenMontage), trimmed to a standalone client.

Authentication uses a key + secret pair from https://cloud.higgsfield.ai/api-keys:
    Authorization: Bearer <HIGGSFIELD_API_KEY>
    X-API-Secret:  <HIGGSFIELD_API_SECRET>

The base URL defaults to the Higgsfield Cloud platform surface
(https://platform.higgsfield.ai/v1). Override with HIGGSFIELD_API_BASE if your
account uses a different endpoint.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger("higgsfield")

DEFAULT_BASE_URL = "https://platform.higgsfield.ai/v1"
DEFAULT_MODEL = "seedance_2.0"

# Terminal job states returned by the generations endpoint (case-insensitive).
_SUCCESS_STATES = {"completed"}
_FAILURE_STATES = {"failed", "nsfw", "cancelled", "canceled", "error"}


class HiggsfieldError(Exception):
    """Base class for all client errors."""


class HiggsfieldAuthError(HiggsfieldError):
    """Credentials are missing or rejected."""


class HiggsfieldAPIError(HiggsfieldError):
    """The API returned an error response.

    Carries the HTTP status, the parsed body (when available), and the
    request id for traceability.
    """

    def __init__(self, message: str, *, status: int | None = None,
                 request_id: str | None = None, body: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.request_id = request_id
        self.body = body


class HiggsfieldTimeout(HiggsfieldError):
    """A generation did not reach a terminal state within the deadline."""


@dataclass
class Generation:
    """The terminal result of a generation job."""

    id: str
    status: str
    output_url: str | None
    raw: dict[str, Any]

    @property
    def succeeded(self) -> bool:
        return self.status.lower() in _SUCCESS_STATES


class HiggsfieldClient:
    """Thin, retrying client for the Higgsfield Cloud API.

    Example:
        client = HiggsfieldClient.from_env()
        gen_id = client.submit_generation("a neon city at night", model="seedance_2.0")
        # ... persist gen_id so the job survives a process restart ...
        result = client.wait_for_generation(gen_id)
        if result.succeeded:
            client.download(result.output_url, "out.mp4")
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        *,
        base_url: str | None = None,
        max_retries: int = 4,
        backoff_base: float = 2.0,
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        if not api_key or not api_secret:
            raise HiggsfieldAuthError(
                "api_key and api_secret are required. Get them at "
                "https://cloud.higgsfield.ai/api-keys"
            )
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = (base_url or os.environ.get("HIGGSFIELD_API_BASE") or DEFAULT_BASE_URL).rstrip("/")
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.timeout = timeout
        self._session = session or requests.Session()

    @classmethod
    def from_env(cls, **kwargs: Any) -> "HiggsfieldClient":
        """Build a client from environment variables.

        Reads HIGGSFIELD_API_KEY + HIGGSFIELD_API_SECRET, or a combined
        HIGGSFIELD_KEY="key:secret".
        """
        combined = os.environ.get("HIGGSFIELD_KEY")
        if combined and ":" in combined:
            api_key, api_secret = combined.split(":", 1)
        else:
            api_key = os.environ.get("HIGGSFIELD_API_KEY", "")
            api_secret = os.environ.get("HIGGSFIELD_API_SECRET", "")
        return cls(api_key, api_secret, **kwargs)

    # -- internal ----------------------------------------------------------

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Secret": self.api_secret,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path_or_url: str, **kwargs: Any) -> dict[str, Any]:
        """Perform a request with exponential backoff on 429 / 5xx.

        Honors a `Retry-After` header when present. Never logs credentials or
        full response bodies; logs the request id for traceability.
        """
        url = path_or_url if path_or_url.startswith("http") else f"{self.base_url}/{path_or_url.lstrip('/')}"
        kwargs.setdefault("timeout", self.timeout)

        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self._session.request(method, url, headers=self._headers, **kwargs)
            except requests.RequestException as exc:
                last_exc = exc
                if attempt == self.max_retries:
                    raise HiggsfieldAPIError(f"network error calling {method} {url}: {exc}") from exc
                self._sleep_backoff(attempt)
                continue

            request_id = resp.headers.get("x-request-id") or resp.headers.get("x-amzn-requestid")

            if resp.status_code == 401 or resp.status_code == 403:
                raise HiggsfieldAuthError(
                    f"authentication rejected (HTTP {resp.status_code}, request_id={request_id})"
                )

            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt == self.max_retries:
                    raise HiggsfieldAPIError(
                        f"{method} {url} failed after {attempt + 1} attempts",
                        status=resp.status_code,
                        request_id=request_id,
                    )
                retry_after = resp.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else None
                logger.warning(
                    "Higgsfield %s %s -> HTTP %s (request_id=%s); retrying (attempt %d/%d)",
                    method, url, resp.status_code, request_id, attempt + 1, self.max_retries,
                )
                self._sleep_backoff(attempt, override=delay)
                continue

            if resp.status_code >= 400:
                body = self._safe_json(resp)
                raise HiggsfieldAPIError(
                    f"{method} {url} returned HTTP {resp.status_code}",
                    status=resp.status_code,
                    request_id=request_id,
                    body=body,
                )

            logger.debug("Higgsfield %s %s -> HTTP %s (request_id=%s)",
                         method, url, resp.status_code, request_id)
            return self._safe_json(resp)

        # Unreachable, but keeps type checkers happy.
        raise HiggsfieldAPIError(f"{method} {url} failed: {last_exc}")

    def _sleep_backoff(self, attempt: int, *, override: float | None = None) -> None:
        time.sleep(override if override is not None else self.backoff_base ** attempt)

    @staticmethod
    def _safe_json(resp: requests.Response) -> dict[str, Any]:
        try:
            return resp.json()
        except ValueError:
            return {}

    # -- public API --------------------------------------------------------

    def submit_generation(
        self,
        prompt: str,
        *,
        model: str = DEFAULT_MODEL,
        operation: str = "text_to_video",
        duration: int | None = None,
        aspect_ratio: str | None = None,
        image_url: str | None = None,
        **extra: Any,
    ) -> str:
        """Submit a generation job and return its id.

        Persist the returned id so the job can be recovered after a restart
        (see CLAUDE.md). Use `wait_for_generation(id)` to await completion.
        """
        if not prompt:
            raise ValueError("prompt is required")

        payload: dict[str, Any] = {
            "prompt": prompt,
            "model": model,
            "task": operation.replace("_", "-"),
        }
        if duration is not None:
            payload["duration"] = int(duration)
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if operation == "image_to_video":
            if not image_url:
                raise ValueError("image_url is required for image_to_video")
            payload["image_url"] = image_url
        payload.update(extra)

        data = self._request("POST", "generations", json=payload)
        gen_id = data.get("id")
        if not gen_id:
            raise HiggsfieldAPIError("submit response missing generation id", body=data)
        logger.info("Submitted Higgsfield generation %s (model=%s)", gen_id, model)
        return gen_id

    def get_generation(self, generation_id: str) -> dict[str, Any]:
        """Fetch the current status payload for a generation."""
        return self._request("GET", f"generations/{generation_id}")

    def wait_for_generation(
        self,
        generation_id: str,
        *,
        poll_interval: float = 5.0,
        timeout: float = 360.0,
    ) -> Generation:
        """Poll a generation until it reaches a terminal state.

        Raises HiggsfieldAPIError on a failure state and HiggsfieldTimeout if
        the deadline elapses first.
        """
        deadline = time.monotonic() + timeout
        while True:
            data = self.get_generation(generation_id)
            status = str(data.get("status", "unknown"))
            normalized = status.lower()

            if normalized in _SUCCESS_STATES:
                output_url = data.get("output_url") or data.get("url")
                return Generation(generation_id, status, output_url, data)
            if normalized in _FAILURE_STATES:
                raise HiggsfieldAPIError(
                    f"generation {generation_id} ended as {status}: {data.get('error', 'unknown')}",
                    body=data,
                )
            if time.monotonic() >= deadline:
                raise HiggsfieldTimeout(
                    f"generation {generation_id} did not finish within {timeout:.0f}s (last status={status})"
                )
            time.sleep(poll_interval)

    def generate_video(
        self,
        prompt: str,
        *,
        output_path: str | os.PathLike[str] | None = None,
        poll_interval: float = 5.0,
        timeout: float = 360.0,
        **submit_kwargs: Any,
    ) -> Generation:
        """Submit a job, wait for it, and optionally download the result.

        Convenience wrapper around submit -> wait -> download. For long-running
        batch work prefer the explicit submit/persist/wait flow so job ids
        survive restarts.
        """
        gen_id = self.submit_generation(prompt, **submit_kwargs)
        result = self.wait_for_generation(gen_id, poll_interval=poll_interval, timeout=timeout)
        if output_path and result.output_url:
            self.download(result.output_url, output_path)
        return result

    def download(self, url: str, output_path: str | os.PathLike[str]) -> Path:
        """Download a generated asset to disk."""
        if not url:
            raise ValueError("url is required")
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        resp = self._session.get(url, timeout=120)
        resp.raise_for_status()
        path.write_bytes(resp.content)
        logger.info("Downloaded Higgsfield asset to %s", path)
        return path
