#!/usr/bin/env python3
"""Submit a Higgsfield video-generation job and wait for the result.

Usage:
    python scripts/generate_video.py "a neon city at night, cinematic"

Requires HIGGSFIELD_API_KEY in the environment (or a local .env file).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from higgsfield import HiggsfieldClient, HiggsfieldError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a video with Higgsfield.")
    parser.add_argument("prompt", help="Text prompt for the video.")
    parser.add_argument(
        "--timeout", type=float, default=600.0, help="Max seconds to wait."
    )
    parser.add_argument(
        "--poll-interval", type=float, default=5.0, help="Seconds between polls."
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        with HiggsfieldClient() as client:
            job = client.generate_and_wait(
                {"prompt": args.prompt},
                poll_interval=args.poll_interval,
                timeout=args.timeout,
            )
    except HiggsfieldError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Job {job.id} completed.")
    if job.output_url:
        print(f"Output: {job.output_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
