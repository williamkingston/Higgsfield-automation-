#!/usr/bin/env python3
"""Validate a batch of Higgsfield jobs and emit the connector request payloads.

Generation runs through the Higgsfield **MCP connector**, which is agent-driven
(a standalone script can't call an MCP tool). So this CLI does the pure-Python
part: it validates every job against the real model catalog and prints the exact
`generate_video` payloads an agent would submit. Feed the jobs file to an agent
session (or a host that bridges the connector) to actually run them.

Usage:
    python scripts/run_batch.py jobs.example.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.client import HiggsfieldConnectorClient, HiggsfieldValidationError


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate jobs and emit connector payloads.")
    parser.add_argument("jobs", help="Path to a JSON file describing the jobs.")
    args = parser.parse_args()

    jobs = json.loads(Path(args.jobs).read_text())
    if not isinstance(jobs, list):
        print("error: jobs file must contain a JSON list", file=sys.stderr)
        return 2

    # A no-op invoker: we only use build_request (no calls are made).
    client = HiggsfieldConnectorClient(invoker=lambda tool, args: {})

    payloads, errors = [], []
    for job in jobs:
        try:
            payload = client.build_request(
                job.get("model", "seedance_2_0"),
                job.get("prompt"),
                **job.get("params", {}),
            )
            payloads.append({"key": job.get("key"), "output": job.get("output"), **payload})
        except HiggsfieldValidationError as exc:
            errors.append({"key": job.get("key"), "error": str(exc)})

    print(json.dumps({"generate_video_payloads": payloads, "errors": errors}, indent=2))
    if errors:
        print(f"\n{len(errors)} job(s) failed validation.", file=sys.stderr)
        return 1
    print(f"\n{len(payloads)} job(s) validated. Submit these via the Higgsfield connector.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
