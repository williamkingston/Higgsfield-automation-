import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import higgsfield_batch  # noqa: E402
from higgsfield import Job  # noqa: E402


def test_read_prompts_txt(tmp_path):
    f = tmp_path / "prompts.txt"
    f.write_text("a neon city\n\n  rain on a window  \n", encoding="utf-8")
    assert higgsfield_batch.read_prompts(f) == ["a neon city", "rain on a window"]


def test_read_prompts_csv(tmp_path):
    f = tmp_path / "prompts.csv"
    f.write_text("prompt,duration\na neon city,5\nrain on a window,5\n", encoding="utf-8")
    assert higgsfield_batch.read_prompts(f) == ["a neon city", "rain on a window"]


def test_read_prompts_csv_missing_column(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text("name,duration\nx,5\n", encoding="utf-8")
    with pytest.raises(ValueError):
        higgsfield_batch.read_prompts(f)


def test_submit_all_submits_every_prompt_up_front():
    client = MagicMock()
    client.create_generation.side_effect = [
        Job(id="job-1", status="queued", raw={}),
        Job(id="job-2", status="queued", raw={}),
    ]

    entries = higgsfield_batch.submit_all(client, ["prompt a", "prompt b"])

    assert [e.job_id for e in entries] == ["job-1", "job-2"]
    assert client.create_generation.call_count == 2
    assert client.get_job.call_count == 0  # no per-job waiting between submits


def test_submit_all_records_per_prompt_failure_without_aborting():
    client = MagicMock()
    client.create_generation.side_effect = [
        higgsfield_batch.HiggsfieldError("boom"),
        Job(id="job-2", status="queued", raw={}),
    ]

    entries = higgsfield_batch.submit_all(client, ["bad prompt", "good prompt"])

    assert entries[0].status == "error"
    assert entries[0].error == "boom"
    assert entries[1].job_id == "job-2"


def test_poll_all_downloads_completed_and_flags_failed(tmp_path, monkeypatch):
    download = MagicMock()
    monkeypatch.setattr(higgsfield_batch, "_download", download)
    client = MagicMock()
    client.get_job.side_effect = [
        Job(id="job-1", status="completed", raw={"output_url": "https://cdn.example.com/a.mp4"}),
        Job(id="job-2", status="failed", raw={}),
    ]
    entries = [
        higgsfield_batch.BatchEntry(prompt="a", job_id="job-1", status="queued"),
        higgsfield_batch.BatchEntry(prompt="b", job_id="job-2", status="queued"),
    ]

    higgsfield_batch.poll_all(client, entries, tmp_path, poll_interval=0, timeout=5)

    assert entries[0].status == "completed"
    assert entries[0].clip == "job-1.mp4"
    assert entries[1].status == "failed"
    download.assert_called_once()


def test_poll_all_times_out_pending_jobs(tmp_path):
    client = MagicMock()
    client.get_job.return_value = Job(id="job-1", status="processing", raw={})
    entries = [higgsfield_batch.BatchEntry(prompt="a", job_id="job-1", status="queued")]

    higgsfield_batch.poll_all(client, entries, tmp_path, poll_interval=0, timeout=0)

    assert entries[0].status == "timeout"
