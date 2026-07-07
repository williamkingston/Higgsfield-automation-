"""Tests for the verified model registry."""

from src.models import (
    DEFAULT_VIDEO_MODEL,
    get_video_model,
    is_valid_video_model,
    suggest_models,
)


def test_real_model_ids_present():
    for mid in ("seedance_2_0", "seedance_2_0_mini", "kling3_0", "veo3_1"):
        assert is_valid_video_model(mid)


def test_speculative_openmontage_ids_absent():
    # These were the wrong ids ported from OpenMontage.
    for mid in ("seedance_2.0", "sora_2", "soul_cinema", "kling_3.0"):
        assert not is_valid_video_model(mid)


def test_default_model_is_valid():
    assert is_valid_video_model(DEFAULT_VIDEO_MODEL)


def test_duration_range_and_options():
    seedance = get_video_model("seedance_2_0")
    assert seedance.duration_ok(5) and seedance.duration_ok(15)
    assert not seedance.duration_ok(20)

    seedance15 = get_video_model("seedance1_5")
    assert seedance15.duration_ok(8)
    assert not seedance15.duration_ok(5)  # discrete options 4/8/12


def test_suggest_maps_dotted_to_underscored():
    suggestions = suggest_models("seedance_2.0")
    assert any("seedance_2_0" in s for s in suggestions)
