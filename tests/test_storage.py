from src.storage import JobStore


def test_upsert_and_read(tmp_path):
    store = JobStore(tmp_path / "jobs.json")
    store.upsert("job-1", {"status": "queued"})
    assert store.all() == {"job-1": {"status": "queued"}}


def test_pending_filters_terminal_states(tmp_path):
    store = JobStore(tmp_path / "jobs.json")
    store.upsert("job-1", {"status": "queued"})
    store.upsert("job-2", {"status": "completed"})
    store.upsert("job-3", {"status": "failed"})

    assert set(store.pending()) == {"job-1"}


def test_persists_across_instances(tmp_path):
    path = tmp_path / "jobs.json"
    JobStore(path).upsert("job-1", {"status": "queued"})

    reopened = JobStore(path)

    assert reopened.all() == {"job-1": {"status": "queued"}}
