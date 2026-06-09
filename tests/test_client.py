"""Tests for the Higgsfield client (mocked HTTP, no network)."""

import pytest
import responses

from src.client import (
    HiggsfieldAPIError,
    HiggsfieldAuthError,
    HiggsfieldClient,
    HiggsfieldTimeout,
)

BASE = "https://platform.higgsfield.ai/v1"


def make_client(**kwargs):
    return HiggsfieldClient("key", "secret", base_url=BASE, backoff_base=0, **kwargs)


def test_requires_credentials():
    with pytest.raises(HiggsfieldAuthError):
        HiggsfieldClient("", "")


def test_from_env_combined(monkeypatch):
    monkeypatch.delenv("HIGGSFIELD_API_KEY", raising=False)
    monkeypatch.delenv("HIGGSFIELD_API_SECRET", raising=False)
    monkeypatch.setenv("HIGGSFIELD_KEY", "abc:xyz")
    client = HiggsfieldClient.from_env()
    assert client.api_key == "abc"
    assert client.api_secret == "xyz"


@responses.activate
def test_submit_sends_auth_and_returns_id():
    responses.add(responses.POST, f"{BASE}/generations", json={"id": "gen_1"}, status=200)
    client = make_client()
    gen_id = client.submit_generation("a cat", model="seedance_2.0", duration=5)

    assert gen_id == "gen_1"
    sent = responses.calls[0].request
    assert sent.headers["Authorization"] == "Bearer key"
    assert sent.headers["X-API-Secret"] == "secret"


@responses.activate
def test_wait_polls_until_completed():
    responses.add(responses.GET, f"{BASE}/generations/gen_1", json={"status": "Processing"}, status=200)
    responses.add(
        responses.GET, f"{BASE}/generations/gen_1",
        json={"status": "Completed", "output_url": "https://cdn/out.mp4"}, status=200,
    )
    client = make_client()
    result = client.wait_for_generation("gen_1", poll_interval=0, timeout=10)

    assert result.succeeded
    assert result.output_url == "https://cdn/out.mp4"


@responses.activate
def test_wait_raises_on_failure_state():
    responses.add(
        responses.GET, f"{BASE}/generations/gen_1",
        json={"status": "Failed", "error": "bad prompt"}, status=200,
    )
    client = make_client()
    with pytest.raises(HiggsfieldAPIError):
        client.wait_for_generation("gen_1", poll_interval=0, timeout=10)


@responses.activate
def test_wait_times_out():
    responses.add(responses.GET, f"{BASE}/generations/gen_1", json={"status": "Processing"}, status=200)
    client = make_client()
    with pytest.raises(HiggsfieldTimeout):
        client.wait_for_generation("gen_1", poll_interval=0, timeout=0)


@responses.activate
def test_retries_on_429_then_succeeds():
    responses.add(responses.POST, f"{BASE}/generations", status=429)
    responses.add(responses.POST, f"{BASE}/generations", json={"id": "gen_2"}, status=200)
    client = make_client(max_retries=2)
    assert client.submit_generation("a dog") == "gen_2"
    assert len(responses.calls) == 2


@responses.activate
def test_auth_error_not_retried():
    responses.add(responses.POST, f"{BASE}/generations", status=401)
    client = make_client(max_retries=3)
    with pytest.raises(HiggsfieldAuthError):
        client.submit_generation("a dog")
    assert len(responses.calls) == 1
