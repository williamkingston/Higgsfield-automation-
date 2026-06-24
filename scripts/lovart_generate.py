#!/usr/bin/env python3
"""Generate a design with Lovart and wait for it to finish.

Usage:
    python scripts/lovart_generate.py "a minimalist logo for a coffee shop"

Reads credentials from the environment (or a local .env file). See
`.env.example` for the required variables.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from lovart import LovartClient, LovartError  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    client = LovartClient()
    try:
        job = client.create_generation(argv[1])
        print(f"Submitted job {job.id} (status: {job.status})")
        job = client.wait_for_job(job.id)
    except LovartError as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1

    if job.succeeded:
        print(f"Job {job.id} completed.")
        return 0
    print(f"Job {job.id} ended with status: {job.status}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
