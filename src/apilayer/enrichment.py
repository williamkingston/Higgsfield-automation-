"""Glue between APILayer clients and the episodic video pipeline.

Nothing here is wired into :class:`higgsfield.pipeline.EpisodePipeline`
automatically — call these explicitly, before generation, for the scenes that
should reflect external data. Results land in ``scene.params["enrichment"]``,
which is free-form and already available to prompt templates via
``Series.build_scene_prompt`` or a custom backend.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from higgsfield.models import Scene

from .screenshotlayer import ScreenshotlayerClient
from .weatherstack import WeatherstackClient


def attach_enrichment(scene: Scene, **data: Any) -> Scene:
    """Merge ``data`` into ``scene.params["enrichment"]`` and return the scene."""
    enrichment = dict(scene.params.get("enrichment", {}))
    enrichment.update(data)
    scene.params["enrichment"] = enrichment
    return scene


def enrich_with_weather(scene: Scene, client: WeatherstackClient, location: str) -> Scene:
    """Attach current weather at ``location`` to the scene.

    Useful for an establishing shot whose prompt should reflect real-world
    conditions in a real place (e.g. "rain-slicked streets of Tokyo tonight").
    """
    current = client.current(location).get("current", {})
    return attach_enrichment(
        scene,
        weather={
            "location": location,
            "description": ", ".join(current.get("weather_descriptions", [])) or None,
            "temperature_c": current.get("temperature"),
        },
    )


def enrich_with_site_capture(
    scene: Scene, client: ScreenshotlayerClient, url: str, out_dir: Path
) -> Scene:
    """Capture ``url`` and attach the saved screenshot path to the scene.

    Feeds the `website-to-hyperframes` capture step's use case (a real
    product screenshot as an ``image_reference``) into this repo's own
    video pipeline.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    image_path = out_dir / f"{scene.id}-capture.png"
    image_path.write_bytes(client.capture(url))
    return attach_enrichment(scene, site_capture={"url": url, "image_path": str(image_path)})
