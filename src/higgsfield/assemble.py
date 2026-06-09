"""Assemble an episode's scene clips into a single video file.

Uses ffmpeg's concat demuxer (stream copy, no re-encode) so assembly is fast and
lossless. Clips should share codec/resolution/fps — which they do when generated
from one series (shared `aspect_ratio` and `default_params`).
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Sequence

logger = logging.getLogger("higgsfield")


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def build_concat_file(clip_paths: Sequence[Path | str], list_path: Path) -> Path:
    """Write an ffmpeg concat-demuxer list file referencing each clip in order."""
    lines = [f"file '{Path(p).resolve().as_posix()}'" for p in clip_paths]
    list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return list_path


def concat_clips(clip_paths: Sequence[Path | str], output_path: Path | str) -> Path:
    """Concatenate clips into `output_path` and return it."""
    if not clip_paths:
        raise ValueError("No clips to concatenate.")
    if not ffmpeg_available():
        raise RuntimeError("ffmpeg not found on PATH; cannot assemble episode.")

    output_path = Path(output_path)
    list_path = output_path.with_suffix(".concat.txt")
    build_concat_file(clip_paths, list_path)
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_path),
        "-c", "copy",
        str(output_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    finally:
        list_path.unlink(missing_ok=True)
    logger.info("Assembled episode: %s", output_path)
    return output_path
