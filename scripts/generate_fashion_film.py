#!/usr/bin/env python3
"""Render (and optionally submit) a 4-shot Silhouette Reveal fashion film.

Usage:
    python scripts/generate_fashion_film.py \\
        --subject-image https://.../model.jpg --subject-desc "male model" \\
        --garment-image https://.../jacket.jpg --garment-desc "gray distressed hooded jacket" \\
        --accessory-image https://.../glasses.jpg --accessory-desc "futuristic silver sunglasses" \\
        --out jobs.json

Add --submit to actually call the Higgsfield API (requires HIGGSFIELD_API_KEY);
without it, prompts are only rendered and saved.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from higgsfield import HiggsfieldClient, HiggsfieldError  # noqa: E402
from templates.fashion_film_silhouette_reveal import (  # noqa: E402
    FilmSubject,
    Reference,
    render_all_shots,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("generate_fashion_film")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--subject-image", required=True, help="URL of the subject/character reference image"
    )
    parser.add_argument(
        "--subject-desc", required=True, help="Descriptive clause, e.g. 'male model'"
    )
    parser.add_argument(
        "--garment-image", required=True, help="URL of the hero garment reference image"
    )
    parser.add_argument(
        "--garment-desc",
        required=True,
        help="Descriptive clause, e.g. 'gray distressed hooded jacket'",
    )
    parser.add_argument(
        "--accessory-image",
        action="append",
        default=[],
        help="URL of an accessory reference image (repeatable)",
    )
    parser.add_argument(
        "--accessory-desc",
        action="append",
        default=[],
        help="Descriptive clause for the accessory at the same position (repeatable)",
    )
    parser.add_argument(
        "--out", default="jobs.json", help="Where to persist rendered prompts / job ids"
    )
    parser.add_argument(
        "--submit", action="store_true", help="Actually submit each shot to the Higgsfield API"
    )
    return parser.parse_args()


def build_subject(args: argparse.Namespace) -> FilmSubject:
    if len(args.accessory_image) != len(args.accessory_desc):
        raise SystemExit(
            "--accessory-image and --accessory-desc must be passed the same number of times"
        )
    return FilmSubject(
        subject=Reference(role=args.subject_desc, description=args.subject_desc),
        garment=Reference(role=args.garment_desc, description=args.garment_desc),
        accessories=[
            Reference(role=desc, description=desc) for desc in args.accessory_desc
        ],
    )


def main() -> int:
    args = parse_args()
    subject = build_subject(args)
    prompts = render_all_shots(subject)

    image_urls = [args.subject_image, args.garment_image, *args.accessory_image]
    results: list[dict[str, object]] = []

    client = HiggsfieldClient() if args.submit else None

    try:
        for i, prompt in enumerate(prompts, start=1):
            entry: dict[str, object] = {"shot": i, "prompt": prompt}
            if client:
                job = client.create_generation(
                    {"prompt": prompt, "reference_image_urls": image_urls}
                )
                entry["job_id"] = job.id
                entry["status"] = job.status
                logger.info("Shot %d submitted as job %s (%s)", i, job.id, job.status)
            results.append(entry)
    except HiggsfieldError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        if client:
            client.close()

    Path(args.out).write_text(json.dumps(results, indent=2))
    logger.info("Wrote %d shots to %s", len(results), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
