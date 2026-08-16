#!/usr/bin/env python3
"""CLI for running a batch of Higgsfield video generations.

Since Higgsfield removed the per-account generation cap, this submits
every request in the input file up front rather than throttling batch
size to conserve quota.

Usage:
    python -m scripts.run_batch --input examples/prompts.example.json --out-dir output/
"""
from __future__ import annotations

import argparse
import json
import logging

from src.batch import BatchRunner, DEFAULT_POLL_INTERVAL_SECONDS
from src.client import HiggsfieldClient
from src.storage import JobStore

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON file containing a list of generation request payloads")
    parser.add_argument("--out-dir", default="output", help="Directory to save downloaded video assets")
    parser.add_argument("--job-store", default="output/jobs.json", help="Path to the persistent job store")
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL_SECONDS)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    client = HiggsfieldClient()
    job_store = JobStore(args.job_store)
    runner = BatchRunner(client, job_store, args.out_dir)

    if job_store.all():
        logger.info("Resuming %d pending job(s) from a previous run", len(job_store.pending()))
    else:
        with open(args.input) as f:
            payloads = json.load(f)
        runner.submit_all(payloads)

    runner.poll_until_complete(poll_interval=args.poll_interval)
    logger.info("Batch complete. %d job(s) tracked in %s", len(job_store.all()), args.job_store)


if __name__ == "__main__":
    main()
