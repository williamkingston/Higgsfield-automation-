"""Tests for the batch runner using a fake connector invoker (no network/spend)."""

from src.batch import BatchRunner
from src.client import HiggsfieldConnectorClient


class FakeInvoker:
    def __init__(self, job_status="Completed", url="https://cdn/a.mp4", cost=10.0):
        self.job_status = job_status
        self.url = url
        self.cost = cost
        self.generate_calls = 0

    def __call__(self, tool, args):
        if tool == "generate_video":
            if args["params"].get("get_cost"):
                return {"cost": {"credits": self.cost, "credits_exact": self.cost}}
            self.generate_calls += 1
            return {"results": [{"job_id": f"job_{self.generate_calls}"}]}
        if tool == "job_display":
            payload = {"status": self.job_status}
            if self.job_status.lower() == "completed":
                payload["output_url"] = self.url
            else:
                payload["error"] = "nsfw"
            return payload
        raise AssertionError(tool)


def make_runner(tmp_path, invoker, record_downloads=None):
    client = HiggsfieldConnectorClient(invoker)
    if record_downloads is not None:
        client.download = lambda url, out: record_downloads.append((url, str(out)))
    return BatchRunner(client, tmp_path / "state.json")


def test_run_completes_and_downloads(tmp_path):
    downloads = []
    runner = make_runner(tmp_path, FakeInvoker(), record_downloads=downloads)
    jobs = [{"key": "a", "model": "seedance_2_0", "prompt": "hi", "output": str(tmp_path / "a.mp4")}]

    states = runner.run(jobs, poll_interval=0, timeout=10)

    assert states["a"].status == "completed"
    assert states["a"].job_id == "job_1"
    assert downloads == [("https://cdn/a.mp4", str(tmp_path / "a.mp4"))]
    assert runner.summary() == {"completed": 1}


def test_failure_recorded(tmp_path):
    runner = make_runner(tmp_path, FakeInvoker(job_status="Failed"))
    runner.run([{"key": "a", "model": "seedance_2_0", "prompt": "x"}], poll_interval=0, timeout=10)
    assert runner.states["a"].status == "failed"


def test_resume_does_not_resubmit(tmp_path):
    inv = FakeInvoker()
    jobs = [{"key": "a", "model": "seedance_2_0", "prompt": "x"}]
    make_runner(tmp_path, inv).run(jobs, poll_interval=0, timeout=10)
    assert inv.generate_calls == 1

    inv2 = FakeInvoker()
    make_runner(tmp_path, inv2).run(jobs, poll_interval=0, timeout=10)
    assert inv2.generate_calls == 0  # completed job must not be re-submitted


def test_state_persisted_between_instances(tmp_path):
    make_runner(tmp_path, FakeInvoker()).run(
        [{"key": "a", "model": "seedance_2_0", "prompt": "x"}], poll_interval=0, timeout=10)
    reloaded = make_runner(tmp_path, FakeInvoker())
    assert reloaded.states["a"].status == "completed"
    assert reloaded.states["a"].job_id == "job_1"


def test_preflight_total_sums_cost(tmp_path):
    runner = make_runner(tmp_path, FakeInvoker(cost=12.5))
    runner._ensure_states([
        {"key": "a", "model": "seedance_2_0", "prompt": "x"},
        {"key": "b", "model": "seedance_2_0_mini", "prompt": "y"},
    ])
    assert runner.preflight_total() == 25.0
