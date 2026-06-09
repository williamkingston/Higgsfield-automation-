#!/usr/bin/env python3
"""CLI: run a batch of Higgsfield generation jobs from a JSON file.

Usage:
    python scripts/run_batch.py jobs.json [--state pipeline/batch_state.json]

The jobs file is a list of objects:
    [
      {"key": "intro", "prompt": "a neon city at night",
       "output": "output/intro.mp4", "params": {"model": "seedance_2.0", "duration": 5}}
    ]

Re-running with the same state file resumes: completed jobs are skipped and
in-flight jobs are recovered by id.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Allow running as a standalone script (python scripts/run_batch.py ...).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.batch import BatchRunner
from src.client import HiggsfieldClient


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a batch of Higgsfield jobs.")
    parser.add_argument("jobs", help="Path to a JSON file describing the jobs.")
    parser.add_argument("--state", default="pipeline/batch_state.json",
                        help="Where to persist job state (default: pipeline/batch_state.json).")
    parser.add_argument("--poll-interval", type=float, default=5.0)
    parser.add_argument("--timeout", type=float, default=1800.0)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    jobs = json.loads(Path(args.jobs).read_text())
    if not isinstance(jobs, list):
        print("error: jobs file must contain a JSON list", file=sys.stderr)
        return 2

    client = HiggsfieldClient.from_env()
    runner = BatchRunner(client, args.state)
    runner.run(jobs, poll_interval=args.poll_interval, timeout=args.timeout)

    summary = runner.summary()
    print(f"Batch finished: {summary}")
    return 1 if summary.get("failed") else 0


if __name__ == "__main__":
    raise SystemExit(main())
