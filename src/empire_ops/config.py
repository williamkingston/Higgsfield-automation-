"""Environment configuration for Empire Ops routines.

Loads ``.env`` if present, then reads from the process environment. Validation
happens at this boundary so routines fail fast with a clear message rather than
deep inside an API call.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # dotenv is optional in CI where env is injected directly
    pass

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_BASE_ID = "applx48uo2056erUB"  # Empire Ops, "My First Workspace"
DEFAULT_TIMEZONE = "America/New_York"


def get(name: str, default: str | None = None) -> str | None:
    """Read an environment variable, returning ``default`` if unset or blank."""
    value = os.environ.get(name)
    return value if value else default


def require(name: str) -> str:
    """Read a required environment variable or raise a descriptive error."""
    value = get(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable {name!r}. "
            f"Copy .env.example to .env and fill it in."
        )
    return value


def airtable_api_key() -> str:
    return require("AIRTABLE_API_KEY")


def airtable_base_id() -> str:
    return get("AIRTABLE_BASE_ID", DEFAULT_BASE_ID)


def timezone() -> str:
    return get("EMPIRE_TIMEZONE", DEFAULT_TIMEZONE)
