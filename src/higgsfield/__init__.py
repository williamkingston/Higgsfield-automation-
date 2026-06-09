"""Higgsfield automation: generate episodic AI video series."""

from .assemble import concat_clips, ffmpeg_available
from .backends import (
    Backend,
    GenerationResult,
    HiggsfieldBackend,
    LTXVideoBackend,
    build_backend,
)
from .client import HiggsfieldClient, HiggsfieldError, Job, JobFailedError
from .config import Config, resolve_output_dir
from .models import Episode, Scene, Series
from .pipeline import EpisodePipeline

__all__ = [
    "Backend",
    "Config",
    "Episode",
    "EpisodePipeline",
    "GenerationResult",
    "HiggsfieldBackend",
    "HiggsfieldClient",
    "HiggsfieldError",
    "Job",
    "JobFailedError",
    "LTXVideoBackend",
    "Scene",
    "Series",
    "build_backend",
    "concat_clips",
    "ffmpeg_available",
    "resolve_output_dir",
]
