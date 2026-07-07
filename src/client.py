"""Higgsfield connector client.

The Higgsfield **MCP connector** is the validated path for generation (it is
authorized per-session via OAuth and proven live). An MCP connector cannot be
called from plain Python, so this client is *transport-injected*: you pass an
`invoker(tool_name, arguments) -> dict` that performs the actual connector call.

- In an agent session, the invoker forwards to the Higgsfield MCP tools
  (`generate_video`, `job_display`, `show_generations`).
- In tests, the invoker is a fake dict-returning function — no network, no spend.

This module owns the parts that are pure Python and fully testable: building and
validating `generate_video` requests against the real model catalog
(`src/models.py`), preflighting cost, and interpreting job responses. Model ids,
the `{"params": {...}}` request envelope, and the `get_cost` response
(`{"cost": {"credits": N}}`) were verified against the live connector.

Example (agent wiring)::

    def invoker(tool, args):
        return call_mcp_tool(f"Higgsfield.{tool}", args)   # host-specific

    client = HiggsfieldConnectorClient(invoker)
    cost = client.preflight_cost("seedance_2_0_mini", "a calm ocean", duration=5)
    job_ids = client.submit("seedance_2_0", "a neon city", duration=5)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import requests

from src.models import (
    DEFAULT_VIDEO_MODEL,
    get_video_model,
    suggest_models,
)

logger = logging.getLogger("higgsfield")

# (tool_name, arguments) -> parsed JSON response dict.
Invoker = Callable[[str, dict[str, Any]], dict[str, Any]]

# Response field names the connector may use for a job id / status / result url.
_JOB_ID_FIELDS = ("job_id", "id", "generation_id")
_STATUS_FIELDS = ("status", "state")
_URL_FIELDS = ("output_url", "url", "video_url", "result_url")
_SUCCESS_STATES = {"completed", "succeeded", "success", "done"}
_FAILURE_STATES = {"failed", "error", "nsfw", "cancelled", "canceled"}


class HiggsfieldError(Exception):
    """Base class for all client errors."""


class HiggsfieldValidationError(HiggsfieldError, ValueError):
    """A request was invalid before it reached the connector."""


class HiggsfieldAPIError(HiggsfieldError):
    """The connector returned an error or unusable response."""


class HiggsfieldTimeout(HiggsfieldError):
    """A job did not reach a terminal state within the deadline."""


@dataclass
class Generation:
    id: str
    status: str
    output_url: str | None
    raw: dict[str, Any]

    @property
    def succeeded(self) -> bool:
        return self.status.lower() in _SUCCESS_STATES


class HiggsfieldConnectorClient:
    """Build, submit, and track Higgsfield connector generations."""

    def __init__(self, invoker: Invoker, *, session: requests.Session | None = None) -> None:
        if not callable(invoker):
            raise HiggsfieldValidationError("invoker must be callable")
        self.invoke = invoker
        self._session = session or requests.Session()

    # -- request building --------------------------------------------------

    def build_request(
        self,
        model: str,
        prompt: str | None = None,
        *,
        duration: int | None = None,
        aspect_ratio: str | None = None,
        medias: list[dict[str, str]] | None = None,
        count: int = 1,
        get_cost: bool = False,
        **extra: Any,
    ) -> dict[str, Any]:
        """Assemble and validate a `generate_video` payload against the catalog."""
        spec = get_video_model(model)
        if spec is None:
            raise HiggsfieldValidationError(
                f"unknown model {model!r}. Did you mean: {', '.join(suggest_models(model))}?"
            )
        if duration is not None and not spec.duration_ok(duration):
            raise HiggsfieldValidationError(
                f"{model} supports {spec.allowed_durations()}, got {duration}s"
            )
        if aspect_ratio and spec.aspect_ratios and aspect_ratio not in spec.aspect_ratios:
            raise HiggsfieldValidationError(
                f"{model} supports aspect ratios {list(spec.aspect_ratios)}, got {aspect_ratio!r}"
            )
        if not (1 <= count <= 4):
            raise HiggsfieldValidationError("count must be between 1 and 4")

        params: dict[str, Any] = {"model": model, "count": count}
        if prompt:
            params["prompt"] = prompt
        if duration is not None:
            params["duration"] = duration
        if aspect_ratio:
            params["aspect_ratio"] = aspect_ratio
        if medias:
            params["medias"] = medias
        if get_cost:
            params["get_cost"] = True
        params.update(extra)
        return {"params": params}

    # -- operations --------------------------------------------------------

    def preflight_cost(self, model: str, prompt: str | None = None, **kwargs: Any) -> float:
        """Return the credit cost of a generation without submitting a job.

        Verified response shape: {"cost": {"credits": N, "credits_exact": N}}.
        """
        kwargs.pop("get_cost", None)
        payload = self.build_request(model, prompt, get_cost=True, **kwargs)
        resp = self.invoke("generate_video", payload)
        cost = resp.get("cost", resp)
        credits = cost.get("credits_exact", cost.get("credits"))
        if credits is None:
            raise HiggsfieldAPIError(f"cost preflight returned no credits field: {resp}")
        return float(credits)

    def submit(self, model: str = DEFAULT_VIDEO_MODEL, prompt: str | None = None,
               **kwargs: Any) -> list[str]:
        """Submit a generation and return the resulting job id(s)."""
        payload = self.build_request(model, prompt, **kwargs)
        resp = self.invoke("generate_video", payload)
        ids = self._extract_job_ids(resp)
        if not ids:
            raise HiggsfieldAPIError(f"submit response had no job id: {resp}")
        logger.info("Submitted Higgsfield generation(s): %s (model=%s)", ids, model)
        return ids

    def get_job(self, job_id: str) -> dict[str, Any]:
        """Fetch a job's current payload via the connector."""
        return self.invoke("job_display", {"id": job_id})

    def wait_for_job(self, job_id: str, *, poll: Callable[[str], dict[str, Any]] | None = None,
                     poll_interval: float = 5.0, timeout: float = 600.0,
                     sleep: Callable[[float], None] | None = None) -> Generation:
        """Poll a job until it reaches a terminal state.

        `poll` defaults to `get_job`; inject a custom poller (e.g. one backed by
        `show_generations`) if the host exposes status differently. `sleep` is
        injectable so tests run instantly.
        """
        import time

        poll = poll or self.get_job
        sleep = sleep or time.sleep
        elapsed = 0.0
        while True:
            data = poll(job_id)
            status = self._extract_status(data)
            normalized = status.lower()
            if normalized in _SUCCESS_STATES:
                return Generation(job_id, status, self._extract_url(data), data)
            if normalized in _FAILURE_STATES:
                raise HiggsfieldAPIError(f"job {job_id} ended as {status}: {data}")
            if elapsed >= timeout:
                raise HiggsfieldTimeout(
                    f"job {job_id} did not finish within {timeout:.0f}s (last status={status})"
                )
            sleep(poll_interval)
            elapsed += poll_interval

    def download(self, url: str, output_path: str | Path) -> Path:
        """Download a result asset to disk."""
        if not url:
            raise HiggsfieldValidationError("url is required")
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        resp = self._session.get(url, timeout=120)
        resp.raise_for_status()
        path.write_bytes(resp.content)
        logger.info("Downloaded Higgsfield asset to %s", path)
        return path

    # -- response parsing (defensive; connector envelope may vary) ----------

    @staticmethod
    def _first_field(data: dict[str, Any], fields: tuple[str, ...]) -> Any:
        for f in fields:
            if data.get(f) is not None:
                return data[f]
        # Some responses nest under "result"/"job"/"generation".
        for key in ("result", "job", "generation"):
            nested = data.get(key)
            if isinstance(nested, dict):
                for f in fields:
                    if nested.get(f) is not None:
                        return nested[f]
        return None

    def _extract_job_ids(self, resp: dict[str, Any]) -> list[str]:
        results = resp.get("results") or resp.get("jobs")
        if isinstance(results, list):
            ids = [self._first_field(r, _JOB_ID_FIELDS) for r in results if isinstance(r, dict)]
            ids = [i for i in ids if i]
            if ids:
                return ids
        single = self._first_field(resp, _JOB_ID_FIELDS)
        return [single] if single else []

    def _extract_status(self, data: dict[str, Any]) -> str:
        return str(self._first_field(data, _STATUS_FIELDS) or "unknown")

    def _extract_url(self, data: dict[str, Any]) -> str | None:
        url = self._first_field(data, _URL_FIELDS)
        if url:
            return url
        results = data.get("results")
        if isinstance(results, list) and results and isinstance(results[0], dict):
            return self._first_field(results[0], _URL_FIELDS)
        return None
