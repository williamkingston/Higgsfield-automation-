import pytest

from src.bloom import BloomAPIError, BloomClient, BloomConfig, BloomConfigError


class FakeResponse:
    def __init__(self, status_code, json_data=None, headers=None, reason="", content=b"x"):
        self.status_code = status_code
        self._json = json_data
        self.headers = headers or {}
        self.reason = reason
        self.content = content if json_data is None else b"{}"

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json


class FakeSession:
    """Returns queued responses in order and records the requests it received."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def request(self, method, url, headers=None, timeout=None, **kwargs):
        self.calls.append({"method": method, "url": url, "headers": headers, "kwargs": kwargs})
        return self._responses.pop(0)


def make_client(responses):
    config = BloomConfig(api_key="bloom_sk_test", api_base="https://api.bloom.ai")
    session = FakeSession(responses)
    return BloomClient(config=config, session=session), session


def test_from_env_requires_api_key(monkeypatch):
    monkeypatch.delenv("BLOOM_API_KEY", raising=False)
    with pytest.raises(BloomConfigError):
        BloomConfig.from_env()


def test_from_env_reads_values(monkeypatch):
    monkeypatch.setenv("BLOOM_API_KEY", "bloom_sk_abc")
    monkeypatch.setenv("BLOOM_API_BASE", "https://example.test/")
    config = BloomConfig.from_env()
    assert config.api_key == "bloom_sk_abc"
    assert config.api_base == "https://example.test"  # trailing slash trimmed


def test_request_sends_bearer_token_and_builds_url():
    client, session = make_client([FakeResponse(200, {"ok": True})])
    result = client.get("/v1/jobs")
    assert result == {"ok": True}
    call = session.calls[0]
    assert call["url"] == "https://api.bloom.ai/v1/jobs"
    assert call["headers"]["Authorization"] == "Bearer bloom_sk_test"


def test_retries_on_429_then_succeeds(monkeypatch):
    monkeypatch.setattr("src.bloom.client.time.sleep", lambda _: None)
    client, session = make_client(
        [FakeResponse(429, headers={"x-request-id": "req-1"}), FakeResponse(200, {"done": True})]
    )
    assert client.get("/v1/jobs") == {"done": True}
    assert len(session.calls) == 2


def test_raises_on_client_error():
    client, _ = make_client(
        [FakeResponse(404, {"error": "not found"}, headers={"x-request-id": "req-9"})]
    )
    with pytest.raises(BloomAPIError) as excinfo:
        client.get("/v1/jobs/missing")
    assert excinfo.value.status_code == 404
    assert excinfo.value.request_id == "req-9"


def test_does_not_leak_api_key_in_error_message():
    client, _ = make_client([FakeResponse(401, {"error": "unauthorized"})])
    with pytest.raises(BloomAPIError) as excinfo:
        client.get("/v1/jobs")
    assert "bloom_sk_test" not in str(excinfo.value)
