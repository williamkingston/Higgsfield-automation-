"""Configuration loading for the Higgsfield client.

Configuration is read from the environment (optionally seeded from a local
``.env`` file). Secrets never have defaults and are never logged.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .errors import ConfigError

DEFAULT_API_BASE = "https://api.higgsfield.ai"
DEFAULT_OUTPUT_DIR = "output"


@dataclass(frozen=True)
class HiggsfieldConfig:
    """Resolved configuration for talking to the Higgsfield API.

    Attributes:
        api_key: Bearer token used for authentication. Required.
        api_base: Base URL for the API. Trailing slashes are stripped.
        timeout: Per-request timeout in seconds.
        max_retries: Number of retries on retryable responses (429/5xx).
    """

    api_key: str
    api_base: str = DEFAULT_API_BASE
    timeout: float = 30.0
    max_retries: int = 5

    @classmethod
    def from_env(cls, *, load_dotenv_file: bool = True) -> HiggsfieldConfig:
        """Build a config from environment variables.

        Reads ``HIGGSFIELD_API_KEY`` (required) and ``HIGGSFIELD_API_BASE``
        (optional, defaults to the public API). Raises :class:`ConfigError`
        when the key is missing so failures surface at the boundary rather
        than as an opaque 401 later.
        """
        if load_dotenv_file:
            load_dotenv()

        api_key = os.environ.get("HIGGSFIELD_API_KEY", "").strip()
        if not api_key:
            raise ConfigError(
                "HIGGSFIELD_API_KEY is not set. Copy .env.example to .env and "
                "fill it in, or export the variable in your environment."
            )

        api_base = os.environ.get("HIGGSFIELD_API_BASE", "").strip() or DEFAULT_API_BASE

        return cls(api_key=api_key, api_base=api_base.rstrip("/"))

    def __repr__(self) -> str:  # pragma: no cover - trivial
        # Never expose the key, even in logs or tracebacks.
        return f"HiggsfieldConfig(api_base={self.api_base!r}, timeout={self.timeout})"


def resolve_output_dir() -> Path:
    """Directory for generated clips and job records.

    Usable by any backend without requiring API credentials, so the episodic
    pipeline can resolve its output location independently of the API config.
    """
    load_dotenv()
    return Path(os.environ.get("HIGGSFIELD_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))
