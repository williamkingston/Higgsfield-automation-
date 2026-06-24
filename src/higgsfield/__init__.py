"""Higgsfield automation: a single API client plus an episodic video pipeline.

Public surface:

    from higgsfield import HiggsfieldClient, HiggsfieldConfig, Job   # API client
    from higgsfield import Series, Episode, EpisodePipeline          # pipeline
"""

from .assemble import concat_clips, ffmpeg_available
from .backends import (
    Backend,
    GenerationResult,
    HiggsfieldBackend,
    LTXVideoBackend,
    build_backend,
)
from .client import HiggsfieldClient, Job
from .config import HiggsfieldConfig, resolve_output_dir
from .errors import (
    APIError,
    ConfigError,
    HiggsfieldError,
    JobError,
    JobTimeout,
    RateLimitError,
)
from .models import Episode, Scene, Series
from .pipeline import EpisodePipeline

__all__ = [
    # API client
    "HiggsfieldClient",
    "HiggsfieldConfig",
    "Job",
    "HiggsfieldError",
    "ConfigError",
    "APIError",
    "RateLimitError",
    "JobError",
    "JobTimeout",
    "resolve_output_dir",
    # Episodic pipeline
    "Series",
    "Episode",
    "Scene",
    "EpisodePipeline",
    "Backend",
    "HiggsfieldBackend",
    "LTXVideoBackend",
    "GenerationResult",
    "build_backend",
    "concat_clips",
    "ffmpeg_available",
]
