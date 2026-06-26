import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from higgsfield import Scene, Series  # noqa: E402

EXAMPLE = Path(__file__).resolve().parents[1] / "series" / "example-series.yaml"


def test_loads_example_series():
    series = Series.from_yaml(EXAMPLE)
    assert series.title == "The Lighthouse Keeper"
    assert len(series.episodes) == 1
    assert len(series.episode(1).scenes) == 3


def test_scene_prompt_prepends_series_context():
    series = Series.from_yaml(EXAMPLE)
    scene = series.episode(1).scenes[0]
    prompt = series.build_scene_prompt(scene)
    assert "Cinematic" in prompt
    assert "MARA" in prompt
    assert scene.prompt.strip().split()[0] in prompt


def test_missing_episode_raises():
    series = Series.from_yaml(EXAMPLE)
    with pytest.raises(KeyError):
        series.episode(99)


def test_scene_requires_prompt():
    with pytest.raises(ValueError):
        Scene.from_dict(0, {"id": "x"})


def test_episode_requires_scenes():
    with pytest.raises(ValueError):
        Series.from_dict({"title": "T", "episodes": [{"number": 1, "title": "E", "scenes": []}]})
