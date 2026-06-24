import hashlib
import hmac
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
    return LovartConfig(
        access_key="ak_test",
        secret_key="sk_test",
        api_base="https://lgw.lovart.ai",
        api_prefix="/v1/openapi",
    )


# -- Config ------------------------------------------------------------


def test_config_from_env_reads_and_strips():
    env = {
        "LOVART_ACCESS_KEY": " ak_abc ",
        "LOVART_SECRET_KEY": "sk_def",
        "LOVART_API_BASE": "https://example.com/",
    }
    config = LovartConfig.from_env(env)
    assert config.access_key == "ak_abc"
    assert config.secret_key == "sk_def"
    assert config.api_base == "https://example.com"  # trailing slash trimmed
    assert config.api_prefix == "/v1/openapi"  # default


def test_config_from_env_defaults_base():
    config = LovartConfig.from_env({"LOVART_ACCESS_KEY": "ak", "LOVART_SECRET_KEY": "sk"})
    assert config.api_base == "https://lgw.lovart.ai"


def test_config_from_env_missing_credentials():
    with pytest.raises(ValueError) as exc:
        LovartConfig.from_env({"LOVART_ACCESS_KEY": "ak"})
    assert "LOVART_SECRET_KEY" in str(exc.value)


# -- Signing -----------------------------------------------------------


def test_request_is_hmac_signed(monkeypatch):
    monkeypatch.setattr("lovart.client.time.time", lambda: 1_700_000_000)
    session = FakeSession([FakeResponse(200, {"ok": True})])
    client = LovartClient(make_config(), session=session)

    client.request("GET", "/chat/status", params={"thread_id": "t1"})

    headers = session.calls[0]["headers"]
    full_path = "/v1/openapi/chat/status"
    expected_sig = hmac.new(
        b"sk_test", f"GET\n{full_path}\n1700000000".encode(), hashlib.sha256
    ).hexdigest()

    assert headers["X-Access-Key"] == "ak_test"
    assert headers["X-Timestamp"] == "1700000000"
    assert headers["X-Signed-Method"] == "GET"
    assert headers["X-Signed-Path"] == full_path
    assert headers["X-Signature"] == expected_sig
    assert "sk_test" not in headers.values()  # secret never sent verbatim
    assert session.calls[0]["url"] == "https://lgw.lovart.ai/v1/openapi/chat/status"


# -- Retries -----------------------------------------------------------


def test_retries_on_429_then_succeeds(monkeypatch):
    monkeypatch.setattr("lovart.client.time.sleep", lambda _: None)
    session = FakeSession([
        FakeResponse(429, headers={"Retry-After": "0"}),
        FakeResponse(200, {"thread_id": "th_1"}),
    ])
    client = LovartClient(make_config(), session=session)
    result = client.request("POST", "/chat", json={"prompt": "cat", "project_id": "p1"})
    assert result == {"thread_id": "th_1"}
    assert len(session.calls) == 2


def test_raises_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr("lovart.client.time.sleep", lambda _: None)
    session = FakeSession([FakeResponse(503) for _ in range(4)])
    client = LovartClient(make_config(), session=session, max_retries=3)
    with pytest.raises(LovartAPIError) as exc:
        client.request("GET", "/chat/status", params={"thread_id": "t1"})
    assert exc.value.status_code == 503


def test_non_retryable_4xx_raises_immediately():
    session = FakeSession([FakeResponse(401, headers={"x-request-id": "req_9"})])
    client = LovartClient(make_config(), session=session)
    with pytest.raises(LovartAPIError) as exc:
        client.request("GET", "/project/validate", params={"project_id": "p1"})
    assert exc.value.status_code == 401
    assert exc.value.request_id == "req_9"
    assert len(session.calls) == 1  # no retry


# -- Chat / generation ----------------------------------------------


def test_chat_submits_and_returns_thread_id():
    session = FakeSession([FakeResponse(200, {"thread_id": "th_42"})])
    client = LovartClient(make_config(), session=session)
    thread_id = client.chat("a fox", "proj_1", mode="fast")
    assert thread_id == "th_42"
    body = session.calls[0]["json"]
    assert body == {"prompt": "a fox", "project_id": "proj_1", "mode": "fast"}


def test_chat_without_thread_id_raises():
    session = FakeSession([FakeResponse(200, {})])
    client = LovartClient(make_config(), session=session)
    with pytest.raises(LovartError):
        client.chat("no thread", "proj_1")


def test_get_status_and_result():
    session = FakeSession([
        FakeResponse(200, {"status": "running"}),
        FakeResponse(200, {"items": []}),
    ])
    client = LovartClient(make_config(), session=session)
    assert client.get_status("th_1") == "running"
    client.get_result("th_1")
    assert session.calls[0]["params"] == {"thread_id": "th_1"}


def test_wait_for_thread_polls_until_terminal(monkeypatch):
    monkeypatch.setattr("lovart.client.time.sleep", lambda _: None)
    session = FakeSession([
        FakeResponse(200, {"status": "running"}),
        FakeResponse(200, {"status": "done"}),
    ])
    client = LovartClient(make_config(), session=session)
    assert client.wait_for_thread("th_1", poll_interval=0) == "done"


def test_generate_aborted_thread_raises(monkeypatch):
    monkeypatch.setattr("lovart.client.time.sleep", lambda _: None)
    session = FakeSession([
        FakeResponse(200, {"thread_id": "th_1"}),  # chat
        FakeResponse(200, {"status": "abort"}),     # status
        FakeResponse(200, {"items": []}),           # result
    ])
    client = LovartClient(make_config(), session=session)
    with pytest.raises(LovartError):
        client.generate("bad", "proj_1", poll_interval=0)


def test_generate_auto_confirms_then_returns(monkeypatch):
    monkeypatch.setattr("lovart.client.time.sleep", lambda _: None)
    session = FakeSession([
        FakeResponse(200, {"thread_id": "th_1"}),                      # chat
        FakeResponse(200, {"status": "done"}),                          # status (round 1)
        FakeResponse(200, {"items": [], "pending_confirmation": {"x": 1}}),  # result (round 1)
        FakeResponse(200, {"ok": True}),                                # confirm
        FakeResponse(200, {"status": "done"}),                          # status (round 2)
        FakeResponse(200, {"items": [{"type": "artifact",
                                      "artifacts": [{"type": "image", "content": "https://cdn/a.png"}]}]}),
    ])
    client = LovartClient(make_config(), session=session)
    result = client.generate("video please", "proj_1", auto_confirm=True, poll_interval=0)
    assert client.artifact_urls(result) == ["https://cdn/a.png"]


def test_artifact_urls_extraction():
    result = {
        "items": [
            {"type": "text", "text": "hi"},
            {"type": "artifact", "artifacts": [
                {"type": "image", "content": "https://cdn/1.png"},
                {"type": "video", "content": "https://cdn/2.mp4"},
            ]},
        ]
    }
    assert LovartClient.artifact_urls(result) == ["https://cdn/1.png", "https://cdn/2.mp4"]


# -- Projects & mode ------------------------------------------------


def test_create_and_rename_project():
    session = FakeSession([
        FakeResponse(200, {"project_id": "p_new"}),
        FakeResponse(200, {"ok": True}),
    ])
    client = LovartClient(make_config(), session=session)
    created = client.create_project("My Project")
    assert created == {"project_id": "p_new"}
    assert session.calls[0]["json"] == {"project_name": "My Project"}

    client.rename_project("p_new", "Renamed")
    assert session.calls[1]["json"] == {
        "action": "rename", "project_id": "p_new", "project_name": "Renamed"
    }


def test_mode_endpoints():
    session = FakeSession([
        FakeResponse(200, {"unlimited": False}),
        FakeResponse(200, {"ok": True}),
    ])
    client = LovartClient(make_config(), session=session)
    client.query_mode()
    assert session.calls[0]["json"] == {}
    client.set_mode(unlimited=True)
    assert session.calls[1]["json"] == {"unlimited": True}
