"""Episode generation pipeline.

Turns an Episode's scenes into video-generation jobs via a pluggable backend
(Higgsfield API or local LTX-Video), persists each scene's result so a restart
can recover, assembles the clips, and writes a manifest describing the episode.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .assemble import concat_clips, ffmpeg_available
from .backends import Backend
from .models import Episode, Scene, Series

logger = logging.getLogger("higgsfield")


class EpisodePipeline:
    def __init__(self, backend: Backend, output_dir: Path) -> None:
        self._backend = backend
        self._output_dir = Path(output_dir)

    def generate_episode(self, series: Series, episode: Episode) -> Path:
        """Generate every scene in an episode and return the manifest path."""
        ep_dir = self._output_dir / _slug(series.title) / episode.slug
        ep_dir.mkdir(parents=True, exist_ok=True)
        records = _load_records(ep_dir)

        logger.info(
            "Generating %s '%s' (%d scenes)",
            episode.slug,
            episode.title,
            len(episode.scenes),
        )
        for scene in episode.scenes:
            record = records.get(scene.id)
            done = record and record.get("status") == "completed"
            if done and _clip_path(ep_dir, scene).exists():
                logger.info("Scene %s already complete; skipping.", scene.id)
                continue
            records[scene.id] = self._generate_scene(series, episode, scene, ep_dir)
            _save_records(ep_dir, records)

        combined = self._assemble(episode, ep_dir)

        manifest_path = ep_dir / "manifest.json"
        manifest = _build_manifest(series, episode, records)
        manifest["episode_file"] = combined.name if combined else None
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        logger.info("Episode complete: %s", manifest_path)
        return manifest_path

    def _assemble(self, episode: Episode, ep_dir: Path) -> Path | None:
        """Stitch the episode's scene clips into a single video, if possible."""
        clips = [_clip_path(ep_dir, s) for s in episode.scenes if _clip_path(ep_dir, s).exists()]
        if not clips:
            logger.warning("No clips available to assemble for %s.", episode.slug)
            return None
        if not ffmpeg_available():
            logger.warning("ffmpeg not found; skipping episode assembly.")
            return None
        try:
            return concat_clips(clips, ep_dir / "episode.mp4")
        except Exception as exc:  # assembly is best-effort; clips are still on disk.
            logger.warning("Episode assembly failed: %s", exc)
            return None

    def _generate_scene(
        self, series: Series, episode: Episode, scene: Scene, ep_dir: Path
    ) -> dict:
        prompt = series.build_scene_prompt(scene)
        params = {
            "aspect_ratio": series.aspect_ratio,
            "duration_seconds": scene.duration_seconds,
            **series.default_params,
            **scene.params,
        }
        if scene.motion:
            params["motion"] = scene.motion
        if scene.image_reference:
            params["image_reference"] = scene.image_reference

        logger.info("Scene %s -> %s backend", scene.id, self._backend.name)
        result = self._backend.generate(prompt, _clip_path(ep_dir, scene), **params)

        return {
            "scene_id": scene.id,
            "backend": result.backend,
            "job_id": result.job_id,
            "status": result.status,
            "output_url": result.output_url,
            "clip": result.clip_path.name if result.clip_path else None,
        }


def _slug(text: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in text.lower()).strip("-")


def _clip_path(ep_dir: Path, scene: Scene) -> Path:
    return ep_dir / f"{scene.id}.mp4"


def _records_path(ep_dir: Path) -> Path:
    return ep_dir / "jobs.json"


def _load_records(ep_dir: Path) -> dict:
    path = _records_path(ep_dir)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_records(ep_dir: Path, records: dict) -> None:
    _records_path(ep_dir).write_text(json.dumps(records, indent=2), encoding="utf-8")


def _build_manifest(series: Series, episode: Episode, records: dict) -> dict:
    return {
        "series": series.title,
        "episode": episode.number,
        "title": episode.title,
        "synopsis": episode.synopsis,
        "aspect_ratio": series.aspect_ratio,
        "backend": series.backend,
        "scenes": [records.get(s.id) for s in episode.scenes],
    }
