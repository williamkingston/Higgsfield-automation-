"""Single entry point for all Lovart API calls.

Per the project conventions, every request to Lovart goes through this module
rather than scattering raw HTTP calls across the codebase. The client handles
request signing, retries with exponential backoff on rate limits, and the
chat-thread polling pattern Lovart uses for generation work.

Authentication
--------------
Lovart issues an access-key / secret-key pair (``ak_...`` / ``sk_...``) and
authenticates each request with an HMAC-SHA256 signature. The signature is
computed over ``"{METHOD}\n{PATH}\n{TIMESTAMP}"`` keyed by the secret key, and
sent alongside the access key, timestamp, and signed method/path as headers.
This is the scheme used by Lovart's own OpenAPI skill. All signing lives in
:meth:`LovartClient._signed_headers` — the single place auth is applied.

Generation flow
---------------
1. ``chat(prompt, project_id)`` submits a prompt and returns a ``thread_id``.
2. ``get_status(thread_id)`` reports ``running`` / ``done`` / ``abort``.
3. ``get_result(thread_id)`` returns the finished artifacts.

``generate()`` ties these together: submit, poll to completion, and return the
result (optionally auto-approving high-cost confirmations).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any

import requests

from .config import LovartConfig

logger = logging.getLogger("lovart")

# Endpoint paths (appended to the configured API prefix).
CHAT_PATH = "/chat"
CHAT_CONFIRM_PATH = "/chat/confirm"
CHAT_STATUS_PATH = "/chat/status"
CHAT_RESULT_PATH = "/chat/result"
PROJECT_SAVE_PATH = "/project/save"
PROJECT_VALIDATE_PATH = "/project/validate"
MODE_SET_PATH = "/mode/set"
MODE_QUERY_PATH = "/mode/query"

USER_AGENT = "higgsfield-automation-lovart/1.0"

# Thread lifecycle states returned by /chat/status.
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_ABORT = "abort"
TERMINAL_STATUSES = {STATUS_DONE, STATUS_ABORT}


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


class LovartClient:
    """HTTP client for the Lovart OpenAPI."""

    def __init__(
        self,
        config: LovartConfig | None = None,
        *,
        session: requests.Session | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.config = config or LovartConfig.from_env()
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = session or requests.Session()

    # -- Authentication -------------------------------------------------

    def _signed_headers(self, method: str, full_path: str) -> dict[str, str]:
        """Return HMAC-signed auth headers for ``method`` and ``full_path``.

        Single source of truth for auth — change this method if Lovart's
        scheme differs. Never log the returned values; they authenticate the
        request and the secret key derives the signature.
        """
        timestamp = str(int(time.time()))
        message = f"{method}\n{full_path}\n{timestamp}".encode()
        signature = hmac.new(
            self.config.secret_key.encode(), message, hashlib.sha256
        ).hexdigest()
        return {
            "X-Access-Key": self.config.access_key,
            "X-Timestamp": timestamp,
            "X-Signature": signature,
            "X-Signed-Method": method,
            "X-Signed-Path": full_path,
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
        """Perform a signed request, retrying on 429 and 5xx.

        ``path`` is the endpoint relative to the API prefix (e.g. ``/chat``).
        Returns the parsed JSON body. Raises :class:`LovartAPIError` on a
        non-success status after retries are exhausted.
        """
        method = method.upper()
        full_path = f"{self.config.api_prefix}{path}"
        url = f"{self.config.api_base}{full_path}"

        last_error: LovartAPIError | None = None
        for attempt in range(self.max_retries + 1):
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": USER_AGENT,
                # Signed per attempt so the timestamp stays fresh across retries.
                **self._signed_headers(method, full_path),
            }
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
                logger.debug("Lovart %s %s -> %s (request_id=%s)", method, full_path, response.status_code, request_id)
                if not response.content:
                    return {}
                return response.json()

            retryable = response.status_code == 429 or response.status_code >= 500
            last_error = LovartAPIError(
                f"Lovart API returned {response.status_code} for {method} {full_path}",
                status_code=response.status_code,
                request_id=request_id,
            )

            if retryable and attempt < self.max_retries:
                delay = self._retry_delay(response, attempt)
                logger.warning(
                    "Lovart %s %s -> %s, retrying in %.1fs (attempt %d/%d, request_id=%s)",
                    method, full_path, response.status_code, delay, attempt + 1, self.max_retries, request_id,
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

    # -- Projects -------------------------------------------------------

    def create_project(self, name: str) -> dict[str, Any]:
        """Create a project and return the API response (includes its id)."""
        return self.request("POST", PROJECT_SAVE_PATH, json={"project_name": name})

    def rename_project(self, project_id: str, name: str) -> dict[str, Any]:
        """Rename an existing project."""
        return self.request(
            "POST",
            PROJECT_SAVE_PATH,
            json={"action": "rename", "project_id": project_id, "project_name": name},
        )

    def validate_project(self, project_id: str) -> dict[str, Any]:
        """Validate / look up a project by id."""
        return self.request("GET", PROJECT_VALIDATE_PATH, params={"project_id": project_id})

    # -- Mode (billing) -------------------------------------------------

    def query_mode(self) -> dict[str, Any]:
        """Return the current generation mode (fast credits vs. unlimited queue)."""
        return self.request("POST", MODE_QUERY_PATH, json={})

    def set_mode(self, *, unlimited: bool) -> dict[str, Any]:
        """Switch between fast (``unlimited=False``) and unlimited modes."""
        return self.request("POST", MODE_SET_PATH, json={"unlimited": unlimited})

    # -- Chat / generation ----------------------------------------------

    def chat(
        self,
        prompt: str,
        project_id: str,
        *,
        mode: str | None = None,
        attachments: list[Any] | None = None,
        thread_id: str | None = None,
        tool_config: dict[str, Any] | None = None,
    ) -> str:
        """Submit a prompt to a project and return the ``thread_id``.

        Pass ``thread_id`` to continue an existing conversation. ``mode`` may be
        ``"thinking"`` or ``"fast"``; ``tool_config`` narrows the tools/models
        Lovart may use.
        """
        body: dict[str, Any] = {"prompt": prompt, "project_id": project_id}
        if mode is not None:
            body["mode"] = mode
        if attachments is not None:
            body["attachments"] = attachments
        if thread_id is not None:
            body["thread_id"] = thread_id
        if tool_config is not None:
            body["tool_config"] = tool_config

        data = self.request("POST", CHAT_PATH, json=body)
        result_thread = data.get("thread_id")
        if not result_thread:
            raise LovartError("Lovart /chat response did not include a thread_id")
        return str(result_thread)

    def get_status(self, thread_id: str) -> str:
        """Return the thread status: ``running``, ``done``, or ``abort``."""
        data = self.request("GET", CHAT_STATUS_PATH, params={"thread_id": thread_id})
        return str(data.get("status") or "unknown")

    def get_result(self, thread_id: str) -> dict[str, Any]:
        """Return the finished artifacts for a thread."""
        return self.request("GET", CHAT_RESULT_PATH, params={"thread_id": thread_id})

    def confirm(self, thread_id: str) -> dict[str, Any]:
        """Approve a pending high-cost operation (e.g. video generation)."""
        return self.request("POST", CHAT_CONFIRM_PATH, json={"thread_id": thread_id})

    def wait_for_thread(
        self,
        thread_id: str,
        *,
        poll_interval: float = 3.0,
        timeout: float = 600.0,
    ) -> str:
        """Poll a thread until it reaches a terminal state or ``timeout`` elapses.

        Returns the terminal status (``done`` or ``abort``). Raises
        :class:`LovartError` on timeout.
        """
        deadline = time.monotonic() + timeout
        while True:
            status = self.get_status(thread_id)
            if status in TERMINAL_STATUSES:
                return status
            if time.monotonic() >= deadline:
                raise LovartError(
                    f"Timed out after {timeout:.0f}s waiting for Lovart thread {thread_id} "
                    f"(last status: {status})"
                )
            time.sleep(poll_interval)

    def generate(
        self,
        prompt: str,
        project_id: str,
        *,
        auto_confirm: bool = False,
        poll_interval: float = 3.0,
        timeout: float = 600.0,
        **chat_options: Any,
    ) -> dict[str, Any]:
        """Submit a prompt, wait for completion, and return the result.

        With ``auto_confirm=True``, any ``pending_confirmation`` is approved and
        the thread is awaited again. Raises :class:`LovartError` if the thread
        ends in ``abort``.
        """
        thread_id = self.chat(prompt, project_id, **chat_options)
        deadline = time.monotonic() + timeout

        while True:
            remaining = max(0.0, deadline - time.monotonic())
            status = self.wait_for_thread(thread_id, poll_interval=poll_interval, timeout=remaining)
            result = self.get_result(thread_id)

            if status == STATUS_ABORT:
                raise LovartError(f"Lovart thread {thread_id} ended in 'abort'")

            if result.get("pending_confirmation") and auto_confirm:
                logger.info("Auto-confirming pending operation for thread %s", thread_id)
                self.confirm(thread_id)
                continue

            return result

    @staticmethod
    def artifact_urls(result: dict[str, Any]) -> list[str]:
        """Extract artifact content URLs from a ``/chat/result`` payload."""
        urls: list[str] = []
        for item in result.get("items", []):
            for artifact in item.get("artifacts", []) or []:
                content = artifact.get("content")
                if content:
                    urls.append(content)
        return urls
