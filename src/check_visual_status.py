#!/usr/bin/env python3
"""Poll Blotato for visual creation status."""
import argparse
import json
import time
from client import get_visual_status


def main():
    parser = argparse.ArgumentParser(description="Check visual creation status")
    parser.add_argument("--creation-id", required=True, help="Visual creation ID")
    parser.add_argument("--poll", action="store_true", help="Poll until complete")
    parser.add_argument("--interval", type=int, default=5, help="Poll interval in seconds")
    parser.add_argument("--timeout", type=int, default=300, help="Max wait time in seconds")
    args = parser.parse_args()

    start = time.time()
    while True:
        result = get_visual_status(args.creation_id)
        status = result.get("status", "unknown")

        if not args.poll or status in ("completed", "failed", "error"):
            print(json.dumps(result, indent=2))
            return

        elapsed = time.time() - start
        if elapsed > args.timeout:
            print(f"Timed out after {args.timeout}s. Last status: {status}")
            print(json.dumps(result, indent=2))
            return

        print(f"Status: {status} ({int(elapsed)}s elapsed). Polling again in {args.interval}s...")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
