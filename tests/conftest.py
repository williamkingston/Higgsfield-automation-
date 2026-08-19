"""Shared test fixtures and a fake HTTP session.

The fake session lets the whole client be exercised offline with no API key and
no network, while still driving the real retry/backoff and polling logic.
"""

from __future__ import annotations

import json as jsonlib
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import pytest

# Make ``src`` importable without an editable install.
SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        body: Mapping[str, Any] | None = None,
        *,
        headers: Mapping[str, str] | None = None,
        text: str | None = None,
    ) -> None:
        self.status_code = status_code
        self._body = body
        self.headers = dict(headers or {})
        self._text = text

    @property
    def is_success(self) -> bool:
        return self.status_code < 400

    def json(self) -> Any:
        if self._text is not None:
            return jsonlib.loads(self._text)
        if self._body is None:
            raise ValueError("no JSON body")
        return self._body


class FakeSession:
    """A requests.Session stand-in that replays a queue of responses."""

    def __init__(self, responses: Iterable[FakeResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(self, method, url, *, json=None, headers=None, timeout=None):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "json": json,
                "headers": dict(headers or {}),
                "timeout": timeout,
            }
        )
        if not self._responses:
            raise AssertionError("FakeSession ran out of queued responses")
        return self._responses.pop(0)

    def close(self) -> None:  # pragma: no cover - trivial
        pass


@pytest.fixture
def no_sleep():
    """A sleep callable that records delays instead of waiting."""
    delays: list[float] = []
    return delays, delays.append
