"""Tests for the batch runner using a fake client (no network)."""

from src.batch import BatchRunner


class FakeClient:
    """Minimal stand-in for HiggsfieldClient.

    `statuses` maps a generation id to a list of status payloads returned on
    successive get_generation calls (the last one repeats).
    """

    def __init__(self, statuses=None, fail_submit_keys=None):
        self.statuses = statuses or {}
        self.fail_submit_keys = fail_submit_keys or set()
        self.submitted = []
        self.downloaded = []
        self._poll_idx = {}
        self._counter = 0

    def submit_generation(self, prompt, **params):
        self._counter += 1
        gen_id = f"gen_{self._counter}"
        self.submitted.append((gen_id, prompt, params))
        return gen_id

    def get_generation(self, generation_id):
        seq = self.statuses.get(generation_id, [{"status": "Completed", "output_url": "https://cdn/x.mp4"}])
        idx = min(self._poll_idx.get(generation_id, 0), len(seq) - 1)
        self._poll_idx[generation_id] = idx + 1
        return seq[idx]

    def download(self, url, output_path):
        self.downloaded.append((url, output_path))


def test_run_completes_and_downloads(tmp_path):
    client = FakeClient(statuses={
        "gen_1": [{"status": "Processing"}, {"status": "Completed", "output_url": "https://cdn/a.mp4"}],
    })
    runner = BatchRunner(client, tmp_path / "state.json")
    jobs = [{"key": "a", "prompt": "hello", "output": str(tmp_path / "a.mp4")}]

    states = runner.run(jobs, poll_interval=0, timeout=10)

    assert states["a"].status == "completed"
    assert states["a"].generation_id == "gen_1"
    assert client.downloaded == [("https://cdn/a.mp4", str(tmp_path / "a.mp4"))]
    assert runner.summary() == {"completed": 1}


def test_failure_state_recorded(tmp_path):
    client = FakeClient(statuses={"gen_1": [{"status": "Failed", "error": "nsfw"}]})
    runner = BatchRunner(client, tmp_path / "state.json")
    runner.run([{"key": "a", "prompt": "x"}], poll_interval=0, timeout=10)

    assert runner.states["a"].status == "failed"
    assert runner.states["a"].error == "nsfw"


def test_resume_does_not_resubmit(tmp_path):
    state_file = tmp_path / "state.json"
    client = FakeClient(statuses={"gen_1": [{"status": "Completed", "output_url": "https://cdn/a.mp4"}]})
    jobs = [{"key": "a", "prompt": "x", "output": str(tmp_path / "a.mp4")}]

    BatchRunner(client, state_file).run(jobs, poll_interval=0, timeout=10)
    assert len(client.submitted) == 1

    # New runner, same state file: the completed job must not be re-submitted.
    client2 = FakeClient()
    BatchRunner(client2, state_file).run(jobs, poll_interval=0, timeout=10)
    assert client2.submitted == []


def test_state_persisted_between_instances(tmp_path):
    state_file = tmp_path / "state.json"
    client = FakeClient(statuses={"gen_1": [{"status": "Completed", "output_url": "https://cdn/a.mp4"}]})
    runner = BatchRunner(client, state_file)
    runner.run([{"key": "a", "prompt": "x"}], poll_interval=0, timeout=10)

    reloaded = BatchRunner(FakeClient(), state_file)
    assert reloaded.states["a"].status == "completed"
    assert reloaded.states["a"].generation_id == "gen_1"
