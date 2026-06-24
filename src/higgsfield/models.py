"""Data models for an episodic AI video series.

A Series contains Episodes; each Episode contains ordered Scenes. A Scene is the
unit handed to the Higgsfield API as a single video-generation job.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Scene:
    """One generated shot within an episode."""

    id: str
    prompt: str
    duration_seconds: float = 5.0
    motion: str | None = None
    image_reference: str | None = None
    params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, index: int, data: dict[str, Any]) -> Scene:
        return cls(
            id=str(data.get("id", f"scene-{index + 1:02d}")),
            prompt=_require(data, "prompt", context=f"scene #{index + 1}"),
            duration_seconds=float(data.get("duration_seconds", 5.0)),
            motion=data.get("motion"),
            image_reference=data.get("image_reference"),
            params=dict(data.get("params", {})),
        )


@dataclass
class Episode:
    number: int
    title: str
    scenes: list[Scene]
    synopsis: str | None = None

    @property
    def slug(self) -> str:
        return f"ep{self.number:02d}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Episode:
        number = int(_require(data, "number", context="episode"))
        scenes_data = data.get("scenes", [])
        if not scenes_data:
            raise ValueError(f"Episode {number} has no scenes.")
        scenes = [Scene.from_dict(i, s) for i, s in enumerate(scenes_data)]
        return cls(
            number=number,
            title=_require(data, "title", context=f"episode {number}"),
            scenes=scenes,
            synopsis=data.get("synopsis"),
        )


@dataclass
class Series:
    """A show: shared style/character context plus a list of episodes."""

    title: str
    style: str | None
    character_bible: str | None
    aspect_ratio: str
    default_params: dict[str, Any]
    episodes: list[Episode]
    backend: str = "higgsfield"
    backend_options: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Series:
        episodes_data = data.get("episodes", [])
        if not episodes_data:
            raise ValueError("Series has no episodes.")
        return cls(
            title=_require(data, "title", context="series"),
            style=data.get("style"),
            character_bible=data.get("character_bible"),
            aspect_ratio=str(data.get("aspect_ratio", "16:9")),
            default_params=dict(data.get("default_params", {})),
            episodes=[Episode.from_dict(e) for e in episodes_data],
            backend=str(data.get("backend", "higgsfield")),
            backend_options=dict(data.get("backend_options", {})),
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> Series:
        with open(path, encoding="utf-8") as handle:
            return cls.from_dict(yaml.safe_load(handle))

    def episode(self, number: int) -> Episode:
        for ep in self.episodes:
            if ep.number == number:
                return ep
        raise KeyError(f"Episode {number} not found in series '{self.title}'.")

    def build_scene_prompt(self, scene: Scene) -> str:
        """Compose the full prompt for a scene, prepending shared series context."""
        parts = [p for p in (self.style, self.character_bible, scene.prompt) if p]
        return " — ".join(parts)


def _require(data: dict[str, Any], key: str, *, context: str) -> Any:
    if key not in data or data[key] in (None, ""):
        raise ValueError(f"Missing required field '{key}' in {context}.")
    return data[key]
