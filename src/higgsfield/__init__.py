"""Higgsfield automation: generate episodic AI video series."""

from .assemble import concat_clips, ffmpeg_available
from .client import HiggsfieldClient, HiggsfieldError, Job, JobFailedError
from .config import Config
from .models import Episode, Scene, Series
from .pipeline import EpisodePipeline

__all__ = [
    "Config",
    "Episode",
    "EpisodePipeline",
    "HiggsfieldClient",
    "HiggsfieldError",
    "Job",
    "JobFailedError",
    "Scene",
    "Series",
    "concat_clips",
    "ffmpeg_available",
]
