from __future__ import annotations

import pytest

from conftest import FakeResponse, FakeSession
from higgsfield.client import HiggsfieldClient
from higgsfield.config import HiggsfieldConfig
from higgsfield.errors import APIError, JobError, JobTimeout, RateLimitError


def make_client(responses, *, max_retries=5):
    config = HiggsfieldConfig(
        api_key="test-key",
        api_base="https://api.test",
        max_retries=max_retries,
    )
    session = FakeSession(responses)
    delays: list[float] = []
    client = HiggsfieldClient(config, session=session, sleep=delays.append)
    return client, session, delays


def test_auth_header_uses_bearer_token():
    client, session, _ = make_client(
        [FakeResponse(200, {"id": "job_1", "status": "pending"})]
    )
    client.create_generation({"prompt": "a cat"})

    auth = session.calls[0]["headers"]["Authorization"]
    assert auth == "Bearer test-key"


def test_create_generation_returns_job():
    client, session, _ = make_client(
        [FakeResponse(201, {"id": "job_42", "status": "queued"})]
    )
    job = client.create_generation({"prompt": "sunset"})

    assert job.id == "job_42"
    assert job.status == "queued"
    assert session.calls[0]["method"] == "POST"
    assert session.calls[0]["url"] == "https://api.test/v1/generations"


def test_retries_on_429_then_succeeds():
    client, session, delays = make_client(
        [
            FakeResponse(429, headers={"Retry-After": "0"}),
            FakeResponse(429, headers={"Retry-After": "0"}),
            FakeResponse(200, {"id": "job_1", "status": "completed"}),
        ]
    )
    job = client.create_generation({"prompt": "x"})

    assert job.is_complete
    assert len(session.calls) == 3
    assert delays == [0.0, 0.0]  # honored Retry-After both times


def test_rate_limit_error_after_exhausting_retries():
    client, _, _ = make_client(
        [FakeResponse(429, headers={"Retry-After": "0"})] * 3,
        max_retries=2,
    )
    with pytest.raises(RateLimitError) as exc:
        client.create_generation({"prompt": "x"})

    assert exc.value.status_code == 429


def test_retries_on_5xx():
    client, session, _ = make_client(
        [
            FakeResponse(503),
            FakeResponse(200, {"id": "job_9", "status": "completed"}),
        ]
    )
    job = client.create_generation({"prompt": "x"})

    assert job.id == "job_9"
    assert len(session.calls) == 2


def test_non_retryable_error_raises_immediately():
    client, session, _ = make_client([FakeResponse(400)])
    with pytest.raises(APIError) as exc:
        client.create_generation({"prompt": "x"})

    assert exc.value.status_code == 400
    assert len(session.calls) == 1


def test_request_id_included_in_error(caplog):
    client, _, _ = make_client(
        [FakeResponse(400, headers={"x-request-id": "req-abc"})]
    )
    with pytest.raises(APIError) as exc:
        client.create_generation({"prompt": "x"})

    assert exc.value.request_id == "req-abc"
    assert "req-abc" in str(exc.value)


def test_api_key_never_logged(caplog):
    import logging

    caplog.set_level(logging.DEBUG, logger="higgsfield")
    client, _, _ = make_client(
        [FakeResponse(200, {"id": "j", "status": "completed"})]
    )
    client.create_generation({"prompt": "x"})

    assert "test-key" not in caplog.text


def test_wait_for_job_polls_until_complete():
    client, session, delays = make_client(
        [
            FakeResponse(200, {"id": "job_1", "status": "processing"}),
            FakeResponse(200, {"id": "job_1", "status": "processing"}),
            FakeResponse(200, {"id": "job_1", "status": "completed"}),
        ]
    )
    job = client.wait_for_job("job_1", poll_interval=1.0)

    assert job.is_complete
    assert len(session.calls) == 3
    assert delays == [1.0, 1.0]


def test_wait_for_job_raises_on_failure():
    client, _, _ = make_client(
        [FakeResponse(200, {"id": "job_1", "status": "failed"})]
    )
    with pytest.raises(JobError) as exc:
        client.wait_for_job("job_1")

    assert exc.value.job_id == "job_1"


def test_wait_for_job_times_out(monkeypatch):
    # Drive monotonic time forward so the deadline trips deterministically.
    ticks = iter([0.0, 0.0, 1000.0])
    monkeypatch.setattr("higgsfield.client.time.monotonic", lambda: next(ticks))

    client, _, _ = make_client(
        [FakeResponse(200, {"id": "job_1", "status": "processing"})] * 5
    )
    with pytest.raises(JobTimeout):
        client.wait_for_job("job_1", poll_interval=1.0, timeout=10.0)


def test_generate_and_wait_end_to_end():
    client, session, _ = make_client(
        [
            FakeResponse(201, {"id": "job_77", "status": "queued"}),
            FakeResponse(
                200,
                {
                    "id": "job_77",
                    "status": "completed",
                    "output_url": "https://cdn.test/out.mp4",
                },
            ),
        ]
    )
    job = client.generate_and_wait({"prompt": "a dog"}, poll_interval=0.1)

    assert job.is_complete
    assert job.output_url == "https://cdn.test/out.mp4"


def test_invalid_json_raises_api_error():
    client, _, _ = make_client([FakeResponse(200, text="not json{")])
    with pytest.raises(APIError):
        client.get_job("job_1")


def test_missing_job_id_in_response_raises():
    client, _, _ = make_client([FakeResponse(200, {"status": "queued"})])
    with pytest.raises(APIError):
        client.create_generation({"prompt": "x"})


def test_get_job_requires_id():
    client, _, _ = make_client([])
    with pytest.raises(ValueError):
        client.get_job("")
