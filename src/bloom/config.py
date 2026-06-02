import os
from dataclasses import dataclass

from .errors import BloomConfigError

DEFAULT_BLOOM_API_BASE = "https://api.bloom.ai"


@dataclass(frozen=True)
class BloomConfig:
    """Connection settings for the Bloom API.

    Prefer :meth:`from_env` so credentials come from the environment and never
    from source. The API key is read from ``BLOOM_API_KEY``; the base URL from
    ``BLOOM_API_BASE`` (falling back to the public default).
    """

    api_key: str
    api_base: str = DEFAULT_BLOOM_API_BASE

    @classmethod
    def from_env(cls) -> "BloomConfig":
        api_key = os.environ.get("BLOOM_API_KEY")
        if not api_key:
            raise BloomConfigError(
                "BLOOM_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        api_base = os.environ.get("BLOOM_API_BASE", DEFAULT_BLOOM_API_BASE)
        return cls(api_key=api_key, api_base=api_base.rstrip("/"))
