"""Configuration for the Lovart API client.

Credentials are read from environment variables so that secrets never live
in source control. Use a local ``.env`` file (git-ignored) during development;
see ``.env.example`` for the expected keys.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_API_BASE = "https://api.lovart.ai"


@dataclass(frozen=True)
class LovartConfig:
    """Resolved Lovart credentials and connection settings."""

    api_key: str
    api_base: str = DEFAULT_API_BASE

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> LovartConfig:
        """Build a config from environment variables.

        Raises ``ValueError`` if the API key is missing so failures surface
        at startup rather than on the first API call.
        """
        source = os.environ if env is None else env

        api_key = (source.get("LOVART_API_KEY") or "").strip()
        api_base = (source.get("LOVART_API_BASE") or DEFAULT_API_BASE).strip().rstrip("/")

        if not api_key:
            raise ValueError(
                "Missing required Lovart credential: LOVART_API_KEY. "
                "Set it in your environment or .env file (see .env.example)."
            )

        return cls(api_key=api_key, api_base=api_base)
