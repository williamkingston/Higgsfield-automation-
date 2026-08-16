from unittest.mock import MagicMock

import pytest

from src.client import HiggsfieldAPIError, HiggsfieldClient


def _response(status_code, json_body=None, headers=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = 200 <= status_code < 300
    resp.headers = headers or {}
    resp.content = b"{}" if json_body is not None else b""
    resp.json.return_value = json_body or {}
    resp.text = text
    return resp


def make_client(session):
    return HiggsfieldClient(api_key="test-key", api_base="https://api.example.com", session=session)


def test_requires_api_key(monkeypatch):
    monkeypatch.delenv("HIGGSFIELD_API_KEY", raising=False)
    with pytest.raises(HiggsfieldAPIError):
        HiggsfieldClient(api_key=None, api_base="https://api.example.com")


def test_sends_bearer_token_and_returns_json():
    session = MagicMock()
    session.request.return_value = _response(200, {"job_id": "abc"})
    client = make_client(session)

    result = client.create_video_generation({"prompt": "a cat"})

    assert result == {"job_id": "abc"}
    _, kwargs = session.request.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"


def test_retries_on_429_then_succeeds(monkeypatch):
    monkeypatch.setattr("src.client.time.sleep", lambda _: None)
    session = MagicMock()
    session.request.side_effect = [
        _response(429, headers={"Retry-After": "0"}),
        _response(200, {"status": "completed"}),
    ]
    client = make_client(session)

    result = client.get_job_status("job-1")

    assert result == {"status": "completed"}
    assert session.request.call_count == 2


def test_raises_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr("src.client.time.sleep", lambda _: None)
    session = MagicMock()
    session.request.return_value = _response(429)
    client = make_client(session)

    with pytest.raises(HiggsfieldAPIError):
        client.get_job_status("job-1")


def test_raises_on_client_error():
    session = MagicMock()
    session.request.return_value = _response(400, text="bad request")
    client = make_client(session)

    with pytest.raises(HiggsfieldAPIError):
        client.get_job_status("job-1")
