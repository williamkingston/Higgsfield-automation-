from unittest.mock import MagicMock

from src.batch import BatchRunner
from src.storage import JobStore


def test_submit_all_records_jobs(tmp_path):
    client = MagicMock()
    client.create_video_generation.side_effect = [{"job_id": "job-1"}, {"job_id": "job-2"}]
    store = JobStore(tmp_path / "jobs.json")
    runner = BatchRunner(client, store, tmp_path / "out")

    job_ids = runner.submit_all([{"prompt": "a"}, {"prompt": "b"}])

    assert job_ids == ["job-1", "job-2"]
    assert set(store.all()) == {"job-1", "job-2"}


def test_poll_until_complete_downloads_completed_jobs(tmp_path):
    client = MagicMock()
    client.get_job_status.return_value = {
        "status": "completed",
        "output": {"url": "https://cdn.example.com/video.mp4"},
    }
    store = JobStore(tmp_path / "jobs.json")
    store.upsert("job-1", {"status": "queued", "payload": {"prompt": "a"}})
    runner = BatchRunner(client, store, tmp_path / "out")

    runner.poll_until_complete(poll_interval=0)

    record = store.all()["job-1"]
    assert record["status"] == "completed"
    client.download_asset.assert_called_once()
    assert not store.pending()


def test_poll_records_failure_without_download(tmp_path):
    client = MagicMock()
    client.get_job_status.return_value = {"status": "failed", "error": "boom"}
    store = JobStore(tmp_path / "jobs.json")
    store.upsert("job-1", {"status": "queued", "payload": {"prompt": "a"}})
    runner = BatchRunner(client, store, tmp_path / "out")

    runner.poll_until_complete(poll_interval=0)

    record = store.all()["job-1"]
    assert record["status"] == "failed"
    assert record["error"] == "boom"
    client.download_asset.assert_not_called()
