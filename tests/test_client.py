import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from higgsfield import HiggsfieldClient, JobFailedError  # noqa: E402
from higgsfield.client import HiggsfieldError  # noqa: E402


class FakeResponse:
    def __init__(self, status_code, json_data=None, headers=None):
        self.status_code = status_code
        self._json = json_data or {}
        self.headers = headers or {}

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        return self._json


class FakeSession:
    """Returns queued responses in order, recording each request."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.headers = {}
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self._responses.pop(0)


def _client(session, **kwargs):
    return HiggsfieldClient("k", "https://api.test", session=session, **kwargs)


def test_create_video_job_parses_id():
    session = FakeSession([FakeResponse(200, {"id": "job-1", "status": "queued"})])
    job = _client(session).create_video_job("a prompt", aspect_ratio="16:9")
    assert job.id == "job-1"
    assert not job.is_done


def test_retries_on_429_then_succeeds(monkeypatch):
    monkeypatch.setattr("higgsfield.client.time.sleep", lambda _s: None)
    session = FakeSession([
        FakeResponse(429, headers={"Retry-After": "0"}),
        FakeResponse(200, {"id": "job-2", "status": "queued"}),
    ])
    job = _client(session, max_retries=3).create_video_job("p")
    assert job.id == "job-2"
    assert len(session.calls) == 2


def test_wait_for_job_raises_on_failure(monkeypatch):
    monkeypatch.setattr("higgsfield.client.time.sleep", lambda _s: None)
    session = FakeSession([FakeResponse(200, {"id": "j", "status": "failed"})])
    with pytest.raises(JobFailedError):
        _client(session).wait_for_job("j")


def test_non_retryable_error_raises():
    session = FakeSession([FakeResponse(400, {"error": "bad"})])
    with pytest.raises(HiggsfieldError):
        _client(session).create_video_job("p")
