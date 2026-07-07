"""Tests for the connector client using a fake invoker (no network, no spend)."""

import pytest

from src.client import (
    Generation,
    HiggsfieldAPIError,
    HiggsfieldConnectorClient,
    HiggsfieldTimeout,
    HiggsfieldValidationError,
)


class FakeInvoker:
    """Records calls and returns scripted responses.

    `generate_video_response` is returned for submit calls; `job_statuses` is a
    list of payloads returned on successive `job_display` calls (last repeats).
    """

    def __init__(self, generate_video_response=None, job_statuses=None, cost=12.5):
        self.generate_video_response = generate_video_response or {"results": [{"job_id": "job_1"}]}
        self.job_statuses = job_statuses or [{"status": "Completed", "output_url": "https://cdn/x.mp4"}]
        self.cost = cost
        self.calls = []
        self._job_idx = 0

    def __call__(self, tool, args):
        self.calls.append((tool, args))
        if tool == "generate_video":
            if args["params"].get("get_cost"):
                return {"cost": {"credits": self.cost, "credits_exact": self.cost}}
            return self.generate_video_response
        if tool == "job_display":
            idx = min(self._job_idx, len(self.job_statuses) - 1)
            self._job_idx += 1
            return self.job_statuses[idx]
        raise AssertionError(f"unexpected tool {tool}")


def test_invoker_must_be_callable():
    with pytest.raises(HiggsfieldValidationError):
        HiggsfieldConnectorClient(invoker=None)


def test_build_request_valid_envelope():
    client = HiggsfieldConnectorClient(FakeInvoker())
    payload = client.build_request("seedance_2_0", "a cat", duration=5, aspect_ratio="16:9")
    assert payload == {"params": {
        "model": "seedance_2_0", "count": 1, "prompt": "a cat",
        "duration": 5, "aspect_ratio": "16:9",
    }}


def test_build_request_unknown_model_suggests():
    client = HiggsfieldConnectorClient(FakeInvoker())
    with pytest.raises(HiggsfieldValidationError) as e:
        client.build_request("seedance_2.0", "x")   # the wrong OpenMontage id
    assert "seedance_2_0" in str(e.value)


def test_build_request_rejects_bad_duration_and_aspect():
    client = HiggsfieldConnectorClient(FakeInvoker())
    with pytest.raises(HiggsfieldValidationError):
        client.build_request("seedance_2_0", "x", duration=99)
    with pytest.raises(HiggsfieldValidationError):
        client.build_request("kling3_0", "x", aspect_ratio="21:9")


def test_preflight_cost_parses_credits():
    client = HiggsfieldConnectorClient(FakeInvoker(cost=12.5))
    assert client.preflight_cost("seedance_2_0_mini", "x", duration=5) == 12.5
    tool, args = client.invoke.calls[-1]
    assert args["params"]["get_cost"] is True


def test_submit_extracts_job_id_from_results_and_top_level():
    c1 = HiggsfieldConnectorClient(FakeInvoker(generate_video_response={"results": [{"job_id": "a"}]}))
    assert c1.submit("seedance_2_0", "x") == ["a"]

    c2 = HiggsfieldConnectorClient(FakeInvoker(generate_video_response={"id": "b"}))
    assert c2.submit("seedance_2_0", "x") == ["b"]


def test_submit_no_id_raises():
    client = HiggsfieldConnectorClient(FakeInvoker(generate_video_response={"nothing": True}))
    with pytest.raises(HiggsfieldAPIError):
        client.submit("seedance_2_0", "x")


def test_wait_completes_and_extracts_url():
    inv = FakeInvoker(job_statuses=[{"status": "Processing"}, {"status": "Completed", "url": "https://cdn/y.mp4"}])
    client = HiggsfieldConnectorClient(inv)
    result = client.wait_for_job("job_1", poll_interval=0, timeout=10, sleep=lambda _s: None)
    assert isinstance(result, Generation) and result.succeeded
    assert result.output_url == "https://cdn/y.mp4"


def test_wait_raises_on_failure():
    inv = FakeInvoker(job_statuses=[{"status": "Failed", "error": "nsfw"}])
    client = HiggsfieldConnectorClient(inv)
    with pytest.raises(HiggsfieldAPIError):
        client.wait_for_job("job_1", poll_interval=0, timeout=10, sleep=lambda _s: None)


def test_wait_times_out():
    inv = FakeInvoker(job_statuses=[{"status": "Processing"}])
    client = HiggsfieldConnectorClient(inv)
    with pytest.raises(HiggsfieldTimeout):
        client.wait_for_job("job_1", poll_interval=1, timeout=0, sleep=lambda _s: None)
