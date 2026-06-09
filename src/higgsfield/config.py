"""Runtime configuration loaded from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # dotenv is optional at runtime; env vars may be set directly.
    load_dotenv = None

DEFAULT_API_BASE = "https://api.higgsfield.ai"
DEFAULT_OUTPUT_DIR = "output"


@dataclass(frozen=True)
class Config:
    api_key: str
    api_base: str
    output_dir: Path

    @classmethod
    def from_env(cls) -> "Config":
        if load_dotenv is not None:
            load_dotenv()

        api_key = os.environ.get("HIGGSFIELD_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "HIGGSFIELD_API_KEY is not set. Copy .env.example to .env and add your key."
            )

        api_base = os.environ.get("HIGGSFIELD_API_BASE", DEFAULT_API_BASE).rstrip("/")

        return cls(api_key=api_key, api_base=api_base, output_dir=resolve_output_dir())


def resolve_output_dir() -> Path:
    """Output directory, usable by any backend without requiring API credentials."""
    if load_dotenv is not None:
        load_dotenv()
    return Path(os.environ.get("HIGGSFIELD_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))
