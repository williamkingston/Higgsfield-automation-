"""Shared HTTP plumbing for APILayer's family of single-purpose REST APIs.

APILayer (weatherstack, fixer, aviationstack, screenshotlayer, ...) publishes
dozens of independent products that all follow the same two conventions: an
``access_key`` query parameter for auth, and a JSON failure envelope of
``{"success": false, "error": {"code": ..., "type": ..., "info": ...}}``. This
module implements that shared contract exactly once — retries with backoff on
``429``/``5xx``, error parsing, request logging — so each product module
(``weatherstack.py``, ``fixer.py``, ...) only has to declare its base URL and
its own typed endpoint methods.

Each product requires its own access key (APILayer products are signed up for
and billed independently, even though the calling convention is identical), so
every subclass sets its own ``service_env_name`` (e.g. ``"WEATHERSTACK"``) and
reads ``{service_env_name}_ACCESS_KEY`` / ``{service_env_name}_API_BASE`` from
the environment.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .errors import APILayerAPIError, ConfigError

logger = logging.getLogger("apilayer")

USER_AGENT = "higgsfield-automation-apilayer/1.0"


@dataclass(frozen=True)
class APILayerConfig:
    """Resolved credentials and connection settings for one APILayer product."""

    access_key: str
    base_url: str

    @classmethod
    def from_env(
        cls,
        service: str,
        *,
        default_base_url: str,
        env: dict[str, str] | None = None,
    ) -> APILayerConfig:
        """Build a config for ``service`` (e.g. ``"WEATHERSTACK"``) from the environment.

        Reads ``{service}_ACCESS_KEY`` (required) and ``{service}_API_BASE``
        (optional, overrides ``default_base_url``). Raises :class:`ConfigError`
        when the key is missing so failures surface at construction rather
        than on the first API call.
        """
        source = os.environ if env is None else env
        key_var = f"{service}_ACCESS_KEY"
        base_var = f"{service}_API_BASE"

        access_key = (source.get(key_var) or "").strip()
        if not access_key:
            raise ConfigError(
                f"{key_var} is not set. Copy .env.example to .env and fill it "
                "in, or export the variable in your environment."
            )
        base_url = (source.get(base_var) or default_base_url).strip().rstrip("/")

        return cls(access_key=access_key, base_url=base_url)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        # Never expose the key, even in logs or tracebacks.
        return f"APILayerConfig(base_url={self.base_url!r})"


class APILayerClient:
    """Base HTTP client for a single APILayer product.

    Subclasses set ``default_base_url`` and ``service_env_name`` as class
    attributes and add typed methods that call :meth:`request`; auth,
    retries, and error parsing all live here so subclasses never issue a raw
    HTTP call themselves.
    """

    default_base_url: str = ""
    service_env_name: str = ""

    def __init__(
        self,
        config: APILayerConfig | None = None,
        *,
        session: httpx.Client | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        if not self.service_env_name or not self.default_base_url:
            raise NotImplementedError(
                f"{type(self).__name__} must set service_env_name and default_base_url"
            )
        self.config = config or APILayerConfig.from_env(
            self.service_env_name, default_base_url=self.default_base_url
        )
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = session or httpx.Client()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perform a request, retrying on 429 and 5xx.

        ``path`` is the endpoint relative to the configured base URL (e.g.
        ``/current``). Returns the parsed JSON body. Raises
        :class:`APILayerAPIError` on a non-success HTTP status after retries
        are exhausted, or when the body carries ``"success": false``.
        """
        response = self._request_with_retries(method, path, params=params)
        data = response.json() if response.content else {}
        if isinstance(data, dict) and data.get("success") is False:
            raise self._parse_api_error(data, response.status_code)
        logger.debug("%s %s %s -> %s", self.service_env_name, method, path, response.status_code)
        return data

    def request_raw(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Like :meth:`request`, but for endpoints that return a binary/text
        body on success (screenshots, scraped HTML, GIFs, PDFs) rather than a
        JSON envelope.

        APILayer's binary-returning products still report failures as the
        usual ``{"success": false, "error": {...}}`` JSON, so a JSON content
        type on an otherwise-200 response is treated as an error. Otherwise
        the raw :class:`httpx.Response` is returned for the caller to read
        ``.content`` / ``.text`` from.
        """
        response = self._request_with_retries(method, path, params=params)
        if "application/json" in response.headers.get("content-type", ""):
            data = response.json() if response.content else {}
            if isinstance(data, dict) and data.get("success") is False:
                raise self._parse_api_error(data, response.status_code)
        logger.debug("%s %s %s -> %s", self.service_env_name, method, path, response.status_code)
        return response

    def _request_with_retries(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        method = method.upper()
        url = f"{self.config.base_url}{path}"
        query: dict[str, Any] = dict(params or {})
        query["access_key"] = self.config.access_key

        last_error: APILayerAPIError | None = None
        for attempt in range(self.max_retries + 1):
            response = self._session.request(
                method,
                url,
                params=query,
                headers={"Accept": "application/json", "User-Agent": USER_AGENT},
                timeout=self.timeout,
            )

            if response.status_code < 400:
                return response

            retryable = response.status_code == 429 or response.status_code >= 500
            last_error = APILayerAPIError(
                f"{self.service_env_name} API returned {response.status_code} for {method} {path}",
                status_code=response.status_code,
            )

            if retryable and attempt < self.max_retries:
                delay = self._retry_delay(response, attempt)
                logger.warning(
                    "%s %s %s -> %s, retrying in %.1fs (attempt %d/%d)",
                    self.service_env_name, method, path, response.status_code,
                    delay, attempt + 1, self.max_retries,
                )
                time.sleep(delay)
                continue

            raise last_error

        assert last_error is not None  # loop always sets it before exhausting
        raise last_error

    def _parse_api_error(self, data: dict[str, Any], status_code: int) -> APILayerAPIError:
        error = data.get("error") or {}
        info = error.get("info") or "unknown error"
        error_type = error.get("type")
        message = f"{self.service_env_name} API error"
        if error_type:
            message += f" ({error_type})"
        message += f": {info}"
        return APILayerAPIError(
            message,
            status_code=status_code,
            error_code=error.get("code"),
            error_type=error_type,
        )

    @staticmethod
    def _retry_delay(response: httpx.Response, attempt: int) -> float:
        """Honour a ``Retry-After`` header when present, else exponential backoff."""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return 2.0**attempt
