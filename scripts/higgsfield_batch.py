#!/usr/bin/env python3
"""Batch-generate videos from a flat list of prompts using Higgsfield.

Higgsfield's unlimited-generations tier removes the per-account job cap, so
this submits every prompt as a job up front instead of generating one at a
time, then polls all of them to completion together and writes a JSON
manifest of results (job ids, statuses, output URLs, and downloaded clip
paths). Failures are recorded per-prompt so one bad prompt doesn't abort the
run.

Usage:
    python scripts/higgsfield_batch.py prompts.txt
    python scripts/higgsfield_batch.py prompts.csv --output-dir clips --manifest results.json

Reads prompts from a file (one prompt per line, or a CSV with a `prompt`
column). Reads credentials from the environment (or a local .env file); see
`.env.example`.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import httpx  # noqa: E402

from higgsfield import HiggsfieldClient, HiggsfieldError  # noqa: E402

logger = logging.getLogger("higgsfield.batch")

_TERMINAL_STATUSES = ("completed", "failed", "error", "timeout")


def read_prompts(path: Path) -> list[str]:
    """Read prompts from a .csv (`prompt` column) or newline-delimited text file."""
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None or "prompt" not in reader.fieldnames:
                raise ValueError(f"{path} must have a 'prompt' column")
            return [row["prompt"].strip() for row in reader if row.get("prompt", "").strip()]

    with path.open(encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


@dataclass
class BatchEntry:
    prompt: str
    job_id: str | None = None
    status: str = "pending"
    output_url: str | None = None
    clip: str | None = None
    error: str | None = None


def submit_all(client: HiggsfieldClient, prompts: list[str]) -> list[BatchEntry]:
    """Submit every prompt as a job up front — no batch-size throttling."""
    entries = []
    for index, prompt in enumerate(prompts, start=1):
        entry = BatchEntry(prompt=prompt)
        try:
            job = client.create_generation({"prompt": prompt})
            entry.job_id = job.id
            entry.status = job.status
            logger.info("[%d/%d] Submitted %s", index, len(prompts), job.id)
        except HiggsfieldError as exc:
            entry.status = "error"
            entry.error = str(exc)
            logger.error("[%d/%d] Submit failed: %s", index, len(prompts), exc)
        entries.append(entry)
    return entries


def poll_all(
    client: HiggsfieldClient,
    entries: list[BatchEntry],
    output_dir: Path,
    *,
    poll_interval: float,
    timeout: float,
) -> None:
    """Poll every job until it's terminal, or the shared deadline passes."""
    deadline = time.monotonic() + timeout
    while True:
        pending = [e for e in entries if e.job_id and e.status not in _TERMINAL_STATUSES]
        if not pending:
            return
        if time.monotonic() >= deadline:
            for entry in pending:
                entry.status = "timeout"
            return
        for entry in pending:
            _poll_one(client, entry, output_dir)
        time.sleep(poll_interval)


def _poll_one(client: HiggsfieldClient, entry: BatchEntry, output_dir: Path) -> None:
    job = client.get_job(entry.job_id)
    if job.is_complete:
        entry.status = "completed"
        entry.output_url = job.output_url
        if job.output_url:
            dest = output_dir / f"{job.id}.mp4"
            _download(job.output_url, dest)
            entry.clip = dest.name
    elif job.is_failed:
        entry.status = "failed"
    else:
        entry.status = job.status


def _download(url: str, dest: Path) -> None:
    with httpx.stream("GET", url, timeout=120, follow_redirects=True) as response:
        response.raise_for_status()
        with open(dest, "wb") as handle:
            for chunk in response.iter_bytes(chunk_size=8192):
                handle.write(chunk)
    logger.info("Downloaded %s", dest)


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch-generate Higgsfield videos.")
    parser.add_argument("prompts_file", type=Path, help="Path to prompts (.txt or .csv).")
    parser.add_argument("--output-dir", type=Path, default=Path("output/higgsfield_batch"))
    parser.add_argument("--manifest", type=Path, default=Path("higgsfield_batch_results.json"))
    parser.add_argument("--poll-interval", type=float, default=5.0)
    parser.add_argument(
        "--timeout", type=float, default=600.0, help="Total seconds to wait for all jobs."
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    try:
        prompts = read_prompts(args.prompts_file)
    except (OSError, ValueError) as exc:
        print(f"Could not read prompts: {exc}", file=sys.stderr)
        return 2
    if not prompts:
        print("No prompts found.", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    client = HiggsfieldClient()

    entries = submit_all(client, prompts)
    poll_all(
        client, entries, args.output_dir, poll_interval=args.poll_interval, timeout=args.timeout
    )

    failures = sum(1 for e in entries if e.status in ("error", "failed", "timeout"))
    manifest = {
        "total": len(prompts),
        "failures": failures,
        "results": [asdict(e) for e in entries],
    }
    args.manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {len(entries)} results ({failures} failed) to {args.manifest}")
    return 1 if failures == len(entries) else 0


if __name__ == "__main__":
    raise SystemExit(main())
