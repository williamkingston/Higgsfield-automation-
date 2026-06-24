#!/usr/bin/env python3
"""Generate a design with Lovart and print the resulting artifact URLs.

Usage:
    python scripts/lovart_generate.py "a minimalist logo for a coffee shop"
    python scripts/lovart_generate.py --project-id <id> "your prompt"

Reads credentials from the environment (or a local .env file). See
`.env.example` for the required variables. When no --project-id is given, a new
project is created.
"""

import argparse
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a design with Lovart.")
    parser.add_argument("prompt", help="The design prompt.")
    parser.add_argument("--project-id", help="Existing project id; a new one is created if omitted.")
    parser.add_argument("--mode", choices=["fast", "thinking"], help="Generation mode.")
    parser.add_argument("--auto-confirm", action="store_true", help="Approve high-cost operations automatically.")
    parser.add_argument("--timeout", type=float, default=600.0, help="Seconds to wait for completion.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    client = LovartClient()
    try:
        project_id = args.project_id
        if not project_id:
            project = client.create_project("higgsfield-automation")
            project_id = project.get("project_id") or project.get("id")
            if not project_id:
                print(f"Could not determine project id from response: {project}", file=sys.stderr)
                return 1
            print(f"Created project {project_id}")

        result = client.generate(
            args.prompt,
            project_id,
            mode=args.mode,
            auto_confirm=args.auto_confirm,
            timeout=args.timeout,
        )
    except LovartError as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1

    urls = client.artifact_urls(result)
    if urls:
        print("Artifacts:")
        for url in urls:
            print(f"  {url}")
    else:
        print("Completed, but no artifact URLs were returned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
