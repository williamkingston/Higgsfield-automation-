"""Higgsfield automation package."""

from src.client import (
    Generation,
    HiggsfieldAPIError,
    HiggsfieldConnectorClient,
    HiggsfieldError,
    HiggsfieldTimeout,
    HiggsfieldValidationError,
)
from src.models import VIDEO_MODELS, DEFAULT_VIDEO_MODEL, get_video_model

__all__ = [
    "Generation",
    "HiggsfieldAPIError",
    "HiggsfieldConnectorClient",
    "HiggsfieldError",
    "HiggsfieldTimeout",
    "HiggsfieldValidationError",
    "VIDEO_MODELS",
    "DEFAULT_VIDEO_MODEL",
    "get_video_model",
]
