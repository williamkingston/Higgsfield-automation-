import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from apilayer.base import APILayerClient, APILayerConfig  # noqa: E402
from apilayer.errors import APILayerAPIError, ConfigError  # noqa: E402


class FakeResponse:
    def __init__(self, status_code, json_data=None, headers=None, content=b"{}", text=""):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self.headers = headers or {}
        self.content = content
        self.text = text or ""

    def json(self):
        return self._json


class FakeSession:
    """Records requests and replays a queued list of responses."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def request(self, method, url, params=None, headers=None, timeout=None):
        self.calls.append({"method": method, "url": url, "params": params, "headers": headers})
        return self._responses.pop(0)


class DummyClient(APILayerClient):
    default_base_url = "https://api.dummystack.com"
    service_env_name = "DUMMYSTACK"


def make_config(**overrides):
    defaults = {"access_key": "key_test", "base_url": "https://api.dummystack.com"}
    defaults.update(overrides)
    return APILayerConfig(**defaults)


# -- Config --------------------------------------------------------------


def test_config_from_env_reads_and_strips():
    env = {"DUMMYSTACK_ACCESS_KEY": " key_abc ", "DUMMYSTACK_API_BASE": "https://example.com/"}
    config = APILayerConfig.from_env("DUMMYSTACK", default_base_url="https://default.com", env=env)
    assert config.access_key == "key_abc"
    assert config.base_url == "https://example.com"  # trailing slash trimmed


def test_config_from_env_defaults_base_url():
    config = APILayerConfig.from_env(
        "DUMMYSTACK", default_base_url="https://default.com", env={"DUMMYSTACK_ACCESS_KEY": "k"}
    )
    assert config.base_url == "https://default.com"


def test_config_from_env_missing_key_raises():
    with pytest.raises(ConfigError) as exc:
        APILayerConfig.from_env("DUMMYSTACK", default_base_url="https://default.com", env={})
    assert "DUMMYSTACK_ACCESS_KEY" in str(exc.value)


# -- Auth ------------------------------------------------------------------


def test_request_injects_access_key():
    session = FakeSession([FakeResponse(200, {"success": True, "value": 1})])
    client = DummyClient(make_config(), session=session)

    result = client.request("GET", "/thing", params={"query": "x"})

    assert result == {"success": True, "value": 1}
    call = session.calls[0]
    assert call["params"] == {"query": "x", "access_key": "key_test"}
    assert call["url"] == "https://api.dummystack.com/thing"


# -- Error envelope ----------------------------------------------------------


def test_request_raises_on_success_false():
    session = FakeSession(
        [
            FakeResponse(
                200,
                {
                    "success": False,
                    "error": {"code": 101, "type": "invalid_access_key", "info": "bad key"},
                },
            )
        ]
    )
    client = DummyClient(make_config(), session=session)

    with pytest.raises(APILayerAPIError) as exc:
        client.request("GET", "/thing")

    assert exc.value.error_code == 101
    assert exc.value.error_type == "invalid_access_key"
    assert "bad key" in str(exc.value)


# -- Retries -----------------------------------------------------------------


def test_retries_on_429_then_succeeds(monkeypatch):
    monkeypatch.setattr("apilayer.base.time.sleep", lambda _: None)
    session = FakeSession(
        [
            FakeResponse(429, headers={"Retry-After": "0"}),
            FakeResponse(200, {"success": True, "value": 1}),
        ]
    )
    client = DummyClient(make_config(), session=session)
    result = client.request("GET", "/thing")
    assert result == {"success": True, "value": 1}
    assert len(session.calls) == 2


def test_raises_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr("apilayer.base.time.sleep", lambda _: None)
    session = FakeSession([FakeResponse(503) for _ in range(4)])
    client = DummyClient(make_config(), session=session, max_retries=3)
    with pytest.raises(APILayerAPIError) as exc:
        client.request("GET", "/thing")
    assert exc.value.status_code == 503


def test_non_retryable_status_raises_immediately():
    session = FakeSession([FakeResponse(404)])
    client = DummyClient(make_config(), session=session, max_retries=3)
    with pytest.raises(APILayerAPIError) as exc:
        client.request("GET", "/thing")
    assert exc.value.status_code == 404
    assert len(session.calls) == 1


# -- request_raw ---------------------------------------------------------


def test_request_raw_returns_response_for_binary_body():
    response = FakeResponse(200, headers={"content-type": "image/png"}, content=b"\x89PNG")
    session = FakeSession([response])
    client = DummyClient(make_config(), session=session)
    response = client.request_raw("GET", "/capture")
    assert response.content == b"\x89PNG"


def test_request_raw_raises_on_json_error_body():
    session = FakeSession(
        [
            FakeResponse(
                200,
                json_data={"success": False, "error": {"code": 104, "info": "usage limit reached"}},
                headers={"content-type": "application/json"},
            )
        ]
    )
    client = DummyClient(make_config(), session=session)
    with pytest.raises(APILayerAPIError) as exc:
        client.request_raw("GET", "/capture")
    assert exc.value.error_code == 104
