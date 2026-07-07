"""Higgsfield model registry — a verified subset of the live model catalog.

Sourced from the Higgsfield connector's `models_explore` catalog (verified
2026-06-16). Model ids here are the REAL ids the connector accepts (underscores,
not dots) — unlike the speculative names originally ported from OpenMontage.

Each entry captures the fields needed to build and validate a `generate_video`
request: the id, human name, provider, allowed aspect ratios, duration support
(a (min, max) range or a discrete list), and the notable extra params.

This registry is intentionally a curated subset focused on video generation.
Call `models_explore` via the connector for the full, always-current catalog.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


@dataclass(frozen=True)
class VideoModel:
    id: str
    name: str
    provider: str
    aspect_ratios: tuple[str, ...] = ()
    # Either a (min, max) inclusive range or a tuple of discrete allowed values.
    duration_range: tuple[int, int] | None = None
    duration_options: tuple[int, ...] | None = None
    params: tuple[str, ...] = ()
    tags: tuple[str, ...] = field(default_factory=tuple)

    def duration_ok(self, seconds: int) -> bool:
        if self.duration_options is not None:
            return seconds in self.duration_options
        if self.duration_range is not None:
            lo, hi = self.duration_range
            return lo <= seconds <= hi
        return True  # model imposes no duration constraint we track

    def allowed_durations(self) -> str:
        if self.duration_options is not None:
            return f"one of {list(self.duration_options)}"
        if self.duration_range is not None:
            return f"{self.duration_range[0]}-{self.duration_range[1]}s"
        return "any"


# Verified video models (subset). Defaults chosen to match the connector's own
# guidance: seedance_2_0 for identity, kling3_0 for multi-shot/audio, and
# kling3_0_turbo / seedance_2_0_mini for fast/budget work.
VIDEO_MODELS: dict[str, VideoModel] = {
    m.id: m
    for m in (
        VideoModel("seedance_2_0", "Seedance 2.0", "Bytedance",
                   ("auto", "16:9", "9:16", "4:3", "3:4", "1:1", "21:9"),
                   duration_range=(4, 15),
                   params=("resolution", "mode", "genre", "generate_audio", "bitrate_mode"),
                   tags=("reference", "identity", "audio", "4k")),
        VideoModel("seedance_2_0_mini", "Seedance 2.0 Mini", "Bytedance",
                   ("auto", "16:9", "9:16", "4:3", "3:4", "1:1", "21:9"),
                   duration_range=(4, 15),
                   params=("resolution", "genre", "generate_audio", "bitrate_mode"),
                   tags=("fast", "budget", "audio")),
        VideoModel("seedance1_5", "Seedance 1.5 Pro", "Bytedance",
                   ("auto", "16:9", "9:16", "4:3", "3:4", "1:1", "21:9"),
                   duration_options=(4, 8, 12),
                   params=("resolution", "generate_audio"),
                   tags=("reliable", "motion")),
        VideoModel("kling3_0", "Kling v3.0", "Kling",
                   ("16:9", "9:16", "1:1"), duration_range=(3, 15),
                   params=("mode", "sound"),
                   tags=("multi-shot", "audio", "motion-transfer")),
        VideoModel("kling3_0_turbo", "Kling 3.0 Turbo", "Kling",
                   ("16:9", "9:16", "1:1"), duration_range=(3, 15),
                   params=("resolution",),
                   tags=("fast", "text-to-video", "budget")),
        VideoModel("kling2_6", "Kling 2.6 Video", "Kling",
                   ("16:9", "9:16", "1:1"), duration_options=(5, 10),
                   params=("sound",), tags=("cinematic", "physics")),
        VideoModel("veo3_1", "Google Veo 3.1", "Google",
                   ("16:9", "9:16"), duration_options=(4, 6, 8),
                   params=("quality", "variant"),
                   tags=("ultra-realistic", "cinematic")),
        VideoModel("veo3", "Google Veo 3", "Google",
                   ("16:9", "9:16"), params=("variant",),
                   tags=("cinematic", "reliable", "audio")),
        VideoModel("wan2_7", "Wan 2.7", "Wan",
                   ("16:9", "9:16", "1:1", "4:3", "3:4"), duration_range=(2, 15),
                   params=("resolution",), tags=("audio", "character", "sync")),
        VideoModel("minimax_hailuo", "Minimax Hailuo", "Hailuo",
                   duration_options=(6, 10),
                   params=("variant", "resolution"),
                   tags=("physics", "emotion", "realistic")),
        VideoModel("gemini_omni", "Gemini Omni Flash", "Google",
                   ("16:9", "9:16"), duration_range=(4, 10),
                   params=("resolution",), tags=("audio", "reference")),
        VideoModel("cinematic_studio_3_0", "Cinema Studio Video 3.0", "Higgsfield",
                   ("auto", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"),
                   duration_range=(4, 15),
                   params=("resolution", "genre", "generate_audio"),
                   tags=("cinematic", "premium", "sota")),
    )
}

DEFAULT_VIDEO_MODEL = "seedance_2_0"


def get_video_model(model_id: str) -> VideoModel | None:
    return VIDEO_MODELS.get(model_id)


def is_valid_video_model(model_id: str) -> bool:
    return model_id in VIDEO_MODELS


def suggest_models(query: str, limit: int = 3) -> list[str]:
    """Cheap fuzzy suggestion for an unknown model id (helps error messages)."""
    q = query.lower().replace(".", "_").replace("-", "_")
    scored = []
    for mid in VIDEO_MODELS:
        norm = mid.lower()
        score = sum(1 for part in q.split("_") if part and part in norm)
        if score:
            scored.append((score, mid))
    scored.sort(reverse=True)
    return [mid for _, mid in scored[:limit]] or list(VIDEO_MODELS)[:limit]
