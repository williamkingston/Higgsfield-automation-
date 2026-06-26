#!/usr/bin/env python3
"""Batch-generate Lovart designs from a list of prompts.

Reads prompts from a file (one prompt per line, or a CSV with a ``prompt``
column), submits each to Lovart, waits for completion, and writes a JSON
manifest of results — including thread ids and artifact URLs — to an output
file. Failures are recorded per-prompt so one bad prompt doesn't abort the run.

Usage:
    python scripts/lovart_batch.py prompts.txt
    python scripts/lovart_batch.py prompts.csv --output results.json --mode fast

Reads credentials from the environment (or a local .env file); see
`.env.example`.
"""

import argparse
import csv
import json
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

logger = logging.getLogger("lovart.batch")


def read_prompts(path: Path) -> list[str]:
    """Read prompts from a .csv (``prompt`` column) or newline-delimited text file."""
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None or "prompt" not in reader.fieldnames:
                raise ValueError(f"{path} must have a 'prompt' column")
            return [row["prompt"].strip() for row in reader if row.get("prompt", "").strip()]

    with path.open(encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch-generate Lovart designs.")
    parser.add_argument("prompts_file", type=Path, help="Path to prompts (.txt or .csv).")
    parser.add_argument("--output", type=Path, default=Path("lovart_batch_results.json"))
    parser.add_argument("--project-id", help="Reuse a project; created if omitted.")
    parser.add_argument("--mode", choices=["fast", "thinking"], help="Generation mode.")
    parser.add_argument(
        "--auto-confirm", action="store_true", help="Approve high-cost operations."
    )
    parser.add_argument("--timeout", type=float, default=600.0, help="Per-prompt seconds.")
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

    client = LovartClient()

    project_id = args.project_id
    if not project_id:
        try:
            project = client.create_project("higgsfield-automation-batch")
        except LovartError as exc:
            print(f"Could not create project: {exc}", file=sys.stderr)
            return 1
        project_id = project.get("project_id") or project.get("id")
        if not project_id:
            print(f"Could not determine project id from response: {project}", file=sys.stderr)
            return 1
        logger.info("Created project %s", project_id)

    results = []
    failures = 0
    for index, prompt in enumerate(prompts, start=1):
        logger.info("[%d/%d] Generating: %s", index, len(prompts), prompt)
        entry: dict = {"prompt": prompt}
        try:
            result = client.generate(
                prompt,
                project_id,
                mode=args.mode,
                auto_confirm=args.auto_confirm,
                timeout=args.timeout,
            )
            entry["status"] = "done"
            entry["artifacts"] = client.artifact_urls(result)
        except LovartError as exc:
            failures += 1
            entry["status"] = "error"
            entry["error"] = str(exc)
            logger.error("[%d/%d] Failed: %s", index, len(prompts), exc)
        results.append(entry)

    manifest = {
        "project_id": project_id,
        "total": len(prompts),
        "failures": failures,
        "results": results,
    }
    args.output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {len(results)} results ({failures} failed) to {args.output}")
    return 1 if failures == len(prompts) else 0


if __name__ == "__main__":
    raise SystemExit(main())
