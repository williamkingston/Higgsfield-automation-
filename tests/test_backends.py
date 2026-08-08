import pytest

from higgsfield import (
    HiggsfieldClient,
    HiggsfieldConfig,
    LTXVideoBackend,
    Series,
    backends,
    build_backend,
)
from higgsfield.backends import _resolve_num_frames


def _fake_ltx_repo(tmp_path):
    (tmp_path / "inference.py").write_text("# stub", encoding="utf-8")
    return tmp_path


def test_ltx_build_command_maps_params(tmp_path):
    backend = LTXVideoBackend(_fake_ltx_repo(tmp_path), pipeline_config="configs/x.yaml")
    cmd = backend.build_command(
        "a prompt",
        tmp_path / "out",
        {"aspect_ratio": "9:16", "duration_seconds": 5, "fps": 24, "seed": 7},
    )
    assert cmd[:2] == ["python", "inference.py"]
    assert "--prompt" in cmd and cmd[cmd.index("--prompt") + 1] == "a prompt"
    # 9:16 preset is portrait (height > width)
    assert cmd[cmd.index("--height") + 1] == "1216"
    assert cmd[cmd.index("--width") + 1] == "704"
    assert cmd[cmd.index("--frame_rate") + 1] == "24"
    assert cmd[cmd.index("--seed") + 1] == "7"
    assert cmd[cmd.index("--pipeline_config") + 1] == "configs/x.yaml"


def test_ltx_image_reference_adds_conditioning(tmp_path):
    backend = LTXVideoBackend(_fake_ltx_repo(tmp_path))
    cmd = backend.build_command("p", tmp_path, {"image_reference": "ref.png"})
    assert cmd[cmd.index("--conditioning_media_paths") + 1] == "ref.png"
    assert "--conditioning_start_frames" in cmd


def test_ltx_requires_inference_script(tmp_path):
    with pytest.raises(FileNotFoundError):
        LTXVideoBackend(tmp_path)  # no inference.py


@pytest.mark.parametrize(
    "duration,fps,expected",
    [(5, 24, 121), (1, 30, 33), (6, 24, 145)],
)
def test_num_frames_is_8k_plus_1(duration, fps, expected):
    num_frames, resolved_fps = _resolve_num_frames(
        {"duration_seconds": duration, "fps": fps}
    )
    assert (num_frames - 1) % 8 == 0
    assert num_frames == expected
    assert resolved_fps == fps


def test_build_backend_unknown_raises():
    series = _series_with(backend="nope")
    with pytest.raises(ValueError):
        build_backend(series)


def test_build_backend_ltx_needs_repo_dir(monkeypatch):
    monkeypatch.delenv("LTX_VIDEO_DIR", raising=False)
    series = _series_with(backend="ltx")
    with pytest.raises(RuntimeError):
        build_backend(series)


def test_build_backend_ltx_from_options(tmp_path):
    series = _series_with(
        backend="ltx", backend_options={"repo_dir": str(_fake_ltx_repo(tmp_path))}
    )
    backend = build_backend(series)
    assert isinstance(backend, LTXVideoBackend)


def test_higgsfield_backend_generate(monkeypatch, tmp_path):
    from conftest import FakeResponse, FakeSession  # offline HTTP stubs

    monkeypatch.setattr(backends, "_download", lambda url, dest: dest.write_bytes(b"x"))

    session = FakeSession([
        FakeResponse(200, {"id": "j1", "status": "queued"}),
        FakeResponse(200, {"id": "j1", "status": "completed", "output_url": "http://x/v.mp4"}),
    ])
    client = HiggsfieldClient(
        HiggsfieldConfig(api_key="k", api_base="https://api.test"),
        session=session,
        sleep=lambda _s: None,
    )
    backend = backends.HiggsfieldBackend(client)
    result = backend.generate("p", tmp_path / "scene.mp4", aspect_ratio="16:9")
    assert result.succeeded
    assert result.job_id == "j1"
    assert result.output_url == "http://x/v.mp4"


def _series_with(**overrides):
    data = {
        "title": "T",
        "episodes": [{"number": 1, "title": "E", "scenes": [{"prompt": "p"}]}],
    }
    data.update(overrides)
    return Series.from_dict(data)
