import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from higgsfield.assemble import build_concat_file, concat_clips  # noqa: E402


def test_build_concat_file_lists_clips_in_order(tmp_path):
    clips = [tmp_path / "scene-01.mp4", tmp_path / "scene-02.mp4"]
    for c in clips:
        c.write_bytes(b"x")
    list_path = build_concat_file(clips, tmp_path / "list.txt")

    lines = list_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("file '") and lines[0].endswith("scene-01.mp4'")
    assert lines[1].endswith("scene-02.mp4'")


def test_concat_clips_rejects_empty(tmp_path):
    with pytest.raises(ValueError):
        concat_clips([], tmp_path / "out.mp4")
