#!/usr/bin/env python3
"""Generate an episode (or a whole series) headlessly.

Submits each scene to the backend, polls to completion, downloads the clips, and
assembles them into a single episode.mp4 — no interactive approvals. Requires
HIGGSFIELD_API_KEY in the environment (or .env) for the Higgsfield backend.

Usage:
    python scripts/generate_episode.py series/mythrealm.yaml --episode 1
    python scripts/generate_episode.py series/mythrealm.yaml --all
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
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--episode", type=int, help="Episode number to generate.")
    group.add_argument("--all", action="store_true", help="Generate every episode in the series.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    series = Series.from_yaml(args.series)
    episodes = series.episodes if args.all else [series.episode(args.episode)]

    backend = build_backend(series)
    pipeline = EpisodePipeline(backend, resolve_output_dir())

    import json

    for episode in episodes:
        manifest_path = pipeline.generate_episode(series, episode)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        episode_file = manifest.get("episode_file")
        assembled = manifest_path.parent / episode_file if episode_file else None
        print(f"Episode {episode.number} '{episode.title}': manifest {manifest_path}")
        if assembled:
            print(f"  Assembled episode -> {assembled}")
        else:
            print("  Clips ready (assembly skipped — see manifest for per-scene clips).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
