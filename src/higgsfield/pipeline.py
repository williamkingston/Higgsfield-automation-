"""Episode generation pipeline.

Turns an Episode's scenes into Higgsfield video jobs, persists each job id so a
restart can recover in-flight work, polls to completion, downloads the rendered
clips, and writes a manifest describing the episode.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import requests

from .client import HiggsfieldClient
from .models import Episode, Scene, Series

logger = logging.getLogger("higgsfield")


class EpisodePipeline:
    def __init__(self, client: HiggsfieldClient, output_dir: Path) -> None:
        self._client = client
        self._output_dir = Path(output_dir)

    def generate_episode(self, series: Series, episode: Episode) -> Path:
        """Generate every scene in an episode and return the manifest path."""
        ep_dir = self._output_dir / _slug(series.title) / episode.slug
        ep_dir.mkdir(parents=True, exist_ok=True)
        records = _load_records(ep_dir)

        logger.info("Generating %s '%s' (%d scenes)", episode.slug, episode.title, len(episode.scenes))
        for scene in episode.scenes:
            record = records.get(scene.id)
            if record and record.get("status") == "completed" and _clip_path(ep_dir, scene).exists():
                logger.info("Scene %s already complete; skipping.", scene.id)
                continue
            records[scene.id] = self._generate_scene(series, episode, scene, ep_dir)
            _save_records(ep_dir, records)

        manifest_path = ep_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(_build_manifest(series, episode, records), indent=2),
            encoding="utf-8",
        )
        logger.info("Episode complete: %s", manifest_path)
        return manifest_path

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

        job = self._client.create_video_job(prompt, **params)
        logger.info("Scene %s submitted as job %s", scene.id, job.id)

        job = self._client.wait_for_job(job.id)
        clip_path = _clip_path(ep_dir, scene)
        if job.output_url:
            _download(job.output_url, clip_path)

        return {
            "scene_id": scene.id,
            "job_id": job.id,
            "status": job.status,
            "output_url": job.output_url,
            "clip": clip_path.name if job.output_url else None,
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
        "scenes": [records.get(s.id) for s in episode.scenes],
    }


def _download(url: str, dest: Path) -> None:
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with open(dest, "wb") as handle:
            for chunk in response.iter_content(chunk_size=8192):
                handle.write(chunk)
    logger.info("Downloaded %s", dest)
