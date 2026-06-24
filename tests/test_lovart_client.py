import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lovart import LovartAPIError, LovartClient, LovartConfig, LovartError  # noqa: E402


class FakeResponse:
    def __init__(self, status_code, json_data=None, headers=None, content=b"{}"):
        self.status_code = status_code
        self._json = json_data or {}
        self.headers = headers or {}
        self.content = content

    def json(self):
        return self._json


class FakeSession:
    """Records requests and replays a queued list of responses."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def request(self, method, url, headers=None, json=None, params=None, timeout=None):
        self.calls.append(
            {"method": method, "url": url, "headers": headers, "json": json, "params": params}
        )
        return self._responses.pop(0)


def make_config():
    return LovartConfig(api_key="key_test", api_base="https://api.lovart.ai")


# -- Config ------------------------------------------------------------


def test_config_from_env_reads_and_strips():
    env = {
        "LOVART_API_KEY": " key_abc ",
        "LOVART_API_BASE": "https://example.com/",
    }
    config = LovartConfig.from_env(env)
    assert config.api_key == "key_abc"
    assert config.api_base == "https://example.com"  # trailing slash trimmed


def test_config_from_env_defaults_base():
    config = LovartConfig.from_env({"LOVART_API_KEY": "key"})
    assert config.api_base == "https://api.lovart.ai"


def test_config_from_env_missing_credentials():
    with pytest.raises(ValueError) as exc:
        LovartConfig.from_env({})
    assert "LOVART_API_KEY" in str(exc.value)


# -- Auth headers ------------------------------------------------------


def test_auth_headers_sent_on_request():
    session = FakeSession([FakeResponse(200, {"ok": True})])
    client = LovartClient(make_config(), session=session)
    client.request("GET", "/v1/ping")
    headers = session.calls[0]["headers"]
    assert headers["X-API-Key"] == "key_test"


# -- Retries -----------------------------------------------------------


def test_retries_on_429_then_succeeds(monkeypatch):
    monkeypatch.setattr("lovart.client.time.sleep", lambda _: None)
    session = FakeSession([
        FakeResponse(429, headers={"Retry-After": "0"}),
        FakeResponse(200, {"id": "job_1", "status": "queued"}),
    ])
    client = LovartClient(make_config(), session=session)
    result = client.request("POST", "/v1/designs/generations", json={"prompt": "cat"})
    assert result == {"id": "job_1", "status": "queued"}
    assert len(session.calls) == 2


def test_raises_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr("lovart.client.time.sleep", lambda _: None)
    session = FakeSession([FakeResponse(503) for _ in range(5)])
    client = LovartClient(make_config(), session=session, max_retries=4)
    with pytest.raises(LovartAPIError) as exc:
        client.request("GET", "/v1/designs/generations/job_1")
    assert exc.value.status_code == 503


def test_non_retryable_4xx_raises_immediately():
    session = FakeSession([FakeResponse(401, headers={"x-request-id": "req_9"})])
    client = LovartClient(make_config(), session=session)
    with pytest.raises(LovartAPIError) as exc:
        client.request("GET", "/v1/me")
    assert exc.value.status_code == 401
    assert exc.value.request_id == "req_9"
    assert len(session.calls) == 1  # no retry


# -- Jobs --------------------------------------------------------------


def test_create_generation_returns_job():
    session = FakeSession([FakeResponse(200, {"id": "job_42", "status": "queued"})])
    client = LovartClient(make_config(), session=session)
    job = client.create_generation("a fox", aspect_ratio="16:9")
    assert job.id == "job_42"
    assert job.status == "queued"
    assert not job.is_terminal
    assert session.calls[0]["json"] == {"prompt": "a fox", "aspect_ratio": "16:9"}


def test_wait_for_job_polls_until_terminal(monkeypatch):
    monkeypatch.setattr("lovart.client.time.sleep", lambda _: None)
    session = FakeSession([
        FakeResponse(200, {"id": "job_1", "status": "processing"}),
        FakeResponse(200, {"id": "job_1", "status": "completed"}),
    ])
    client = LovartClient(make_config(), session=session)
    job = client.wait_for_job("job_1", poll_interval=0)
    assert job.succeeded
    assert job.is_terminal


def test_job_response_without_id_raises():
    session = FakeSession([FakeResponse(200, {"status": "queued"})])
    client = LovartClient(make_config(), session=session)
    with pytest.raises(LovartError):
        client.create_generation("no id")
