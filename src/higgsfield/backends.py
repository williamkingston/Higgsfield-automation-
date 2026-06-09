"""Generation backends.

A backend turns a prompt into a video clip written to a given path. Two are
provided:

- ``HiggsfieldBackend`` — calls the hosted Higgsfield API (async job + download).
- ``LTXVideoBackend`` — runs Lightricks' open-source LTX-Video model locally via
  its ``inference.py`` CLI.

The pipeline is backend-agnostic: it builds a prompt and a generic params dict,
then calls ``backend.generate(prompt, clip_path, **params)``.
"""

from __future__ import annotations

import logging
import os
import shlex
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import requests

from .client import HiggsfieldClient
from .config import Config
from .models import Series

logger = logging.getLogger("higgsfield")


@dataclass
class GenerationResult:
    status: str
    clip_path: Path | None
    backend: str
    job_id: str | None = None
    output_url: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == "completed" and self.clip_path is not None


class Backend(ABC):
    name: str

    @abstractmethod
    def generate(self, prompt: str, output_path: Path, **params: Any) -> GenerationResult:
        """Generate one clip for `prompt`, writing the video to `output_path`."""


# --------------------------------------------------------------------------
# Higgsfield (hosted API)
# --------------------------------------------------------------------------

class HiggsfieldBackend(Backend):
    name = "higgsfield"

    def __init__(self, client: HiggsfieldClient) -> None:
        self._client = client

    def generate(self, prompt: str, output_path: Path, **params: Any) -> GenerationResult:
        job = self._client.create_video_job(prompt, **params)
        logger.info("Higgsfield job %s submitted", job.id)
        job = self._client.wait_for_job(job.id)
        clip: Path | None = None
        if job.output_url:
            _download(job.output_url, output_path)
            clip = output_path
        return GenerationResult(
            status=job.status,
            clip_path=clip,
            backend=self.name,
            job_id=job.id,
            output_url=job.output_url,
        )


# --------------------------------------------------------------------------
# LTX-Video (local, open-source)
# --------------------------------------------------------------------------

# Height x Width presets matching LTX-Video's recommended resolutions.
_ASPECT_PRESETS: dict[str, tuple[int, int]] = {
    "16:9": (704, 1216),
    "9:16": (1216, 704),
    "1:1": (768, 768),
    "4:3": (768, 1024),
    "3:4": (1024, 768),
}


class LTXVideoBackend(Backend):
    name = "ltx"

    def __init__(
        self,
        repo_dir: Path | str,
        *,
        python_bin: str = "python",
        pipeline_config: str | None = None,
        extra_args: Sequence[str] | None = None,
    ) -> None:
        self._repo_dir = Path(repo_dir)
        self._python_bin = python_bin
        self._pipeline_config = pipeline_config
        self._extra_args = list(extra_args or [])
        if not (self._repo_dir / "inference.py").exists():
            raise FileNotFoundError(
                f"LTX-Video inference.py not found in {self._repo_dir}. "
                "Clone https://github.com/Lightricks/LTX-Video and point repo_dir at it."
            )

    def generate(self, prompt: str, output_path: Path, **params: Any) -> GenerationResult:
        output_path = Path(output_path)
        raw_dir = output_path.parent / ".ltx-raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        existing = set(raw_dir.glob("*.mp4"))

        cmd = self.build_command(prompt, raw_dir, params)
        logger.info("LTX-Video: %s", " ".join(shlex.quote(c) for c in cmd))
        subprocess.run(cmd, cwd=str(self._repo_dir), check=True)

        produced = _newest_new_file(raw_dir, existing)
        shutil.move(str(produced), str(output_path))
        return GenerationResult(status="completed", clip_path=output_path, backend=self.name)

    def build_command(self, prompt: str, out_dir: Path, params: dict[str, Any]) -> list[str]:
        height, width = _resolve_dimensions(params)
        num_frames, fps = _resolve_num_frames(params)
        cmd = [
            self._python_bin, "inference.py",
            "--prompt", prompt,
            "--output_path", str(out_dir),
            "--height", str(height),
            "--width", str(width),
            "--num_frames", str(num_frames),
            "--frame_rate", str(fps),
        ]
        if "seed" in params:
            cmd += ["--seed", str(int(params["seed"]))]
        config = params.get("pipeline_config", self._pipeline_config)
        if config:
            cmd += ["--pipeline_config", str(config)]
        image_ref = params.get("image_reference")
        if image_ref:
            cmd += [
                "--conditioning_media_paths", str(image_ref),
                "--conditioning_start_frames", "0",
            ]
        cmd += self._extra_args
        return cmd


def _resolve_dimensions(params: dict[str, Any]) -> tuple[int, int]:
    if params.get("height") and params.get("width"):
        return int(params["height"]), int(params["width"])
    preset = _ASPECT_PRESETS.get(str(params.get("aspect_ratio", "16:9")))
    return preset if preset else (704, 1216)


def _resolve_num_frames(params: dict[str, Any]) -> tuple[int, int]:
    """LTX-Video requires num_frames of the form 8k+1; round duration*fps to fit."""
    fps = int(round(float(params.get("fps", params.get("frame_rate", 30)))))
    duration = float(params.get("duration_seconds", 5.0))
    raw = max(1, round(duration * fps))
    k = max(1, round((raw - 1) / 8))
    return k * 8 + 1, fps


def _newest_new_file(directory: Path, before: set[Path]) -> Path:
    candidates = [p for p in directory.glob("*.mp4") if p not in before]
    if not candidates:
        candidates = list(directory.glob("*.mp4"))
    if not candidates:
        raise RuntimeError(f"LTX-Video produced no .mp4 in {directory}.")
    return max(candidates, key=lambda p: p.stat().st_mtime)


# --------------------------------------------------------------------------
# Factory
# --------------------------------------------------------------------------

def build_backend(series: Series) -> Backend:
    """Construct the backend named by `series.backend`."""
    name = (series.backend or "higgsfield").lower()
    opts = series.backend_options

    if name == "higgsfield":
        config = Config.from_env()
        return HiggsfieldBackend(HiggsfieldClient(config.api_key, config.api_base))

    if name in ("ltx", "ltx-video", "ltxvideo"):
        repo_dir = opts.get("repo_dir") or os.environ.get("LTX_VIDEO_DIR")
        if not repo_dir:
            raise RuntimeError(
                "The 'ltx' backend needs the LTX-Video repo path: set "
                "backend_options.repo_dir in the series file or the LTX_VIDEO_DIR env var."
            )
        return LTXVideoBackend(
            repo_dir=repo_dir,
            python_bin=opts.get("python_bin", "python"),
            pipeline_config=opts.get("pipeline_config"),
            extra_args=opts.get("extra_args", []),
        )

    raise ValueError(f"Unknown backend '{series.backend}'. Use 'higgsfield' or 'ltx'.")


def _download(url: str, dest: Path) -> None:
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with open(dest, "wb") as handle:
            for chunk in response.iter_content(chunk_size=8192):
                handle.write(chunk)
    logger.info("Downloaded %s", dest)
