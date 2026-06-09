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

    access_key: str
    secret_key: str
    api_base: str = DEFAULT_API_BASE

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "LovartConfig":
        """Build a config from environment variables.

        Raises ``ValueError`` if either credential is missing so failures
        surface at startup rather than on the first API call.
        """
        source = os.environ if env is None else env

        access_key = (source.get("LOVART_ACCESS_KEY") or "").strip()
        secret_key = (source.get("LOVART_SECRET_KEY") or "").strip()
        api_base = (source.get("LOVART_API_BASE") or DEFAULT_API_BASE).strip().rstrip("/")

        missing = [
            name
            for name, value in (
                ("LOVART_ACCESS_KEY", access_key),
                ("LOVART_SECRET_KEY", secret_key),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                "Missing required Lovart credentials: "
                + ", ".join(missing)
                + ". Set them in your environment or .env file (see .env.example)."
            )

        return cls(access_key=access_key, secret_key=secret_key, api_base=api_base)
