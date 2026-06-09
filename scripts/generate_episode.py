#!/usr/bin/env python3
"""Generate one episode of a series.

Usage:
    python scripts/generate_episode.py series/example-series.yaml --episode 1
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from higgsfield import (  # noqa: E402
    EpisodePipeline,
    Series,
    build_backend,
    resolve_output_dir,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one episode of an AI video series.")
    parser.add_argument("series", help="Path to the series YAML file.")
    parser.add_argument("--episode", type=int, required=True, help="Episode number to generate.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    series = Series.from_yaml(args.series)
    episode = series.episode(args.episode)

    backend = build_backend(series)
    pipeline = EpisodePipeline(backend, resolve_output_dir())
    manifest = pipeline.generate_episode(series, episode)

    print(f"Done. Manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
