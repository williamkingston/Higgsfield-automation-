"""Higgsfield automation client package.

Public surface:

    from higgsfield import HiggsfieldClient, HiggsfieldConfig, Job
"""

from .client import HiggsfieldClient, Job
from .config import HiggsfieldConfig
from .errors import (
    APIError,
    ConfigError,
    HiggsfieldError,
    JobError,
    JobTimeout,
    RateLimitError,
)

__all__ = [
    "HiggsfieldClient",
    "HiggsfieldConfig",
    "Job",
    "HiggsfieldError",
    "ConfigError",
    "APIError",
    "RateLimitError",
    "JobError",
    "JobTimeout",
]
