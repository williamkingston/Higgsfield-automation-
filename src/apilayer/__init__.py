"""Clients for APILayer's family of single-purpose REST APIs.

Every product shares the same calling convention (an ``access_key`` query
parameter, a common JSON error envelope) implemented once in :mod:`.base`.
Each module below is a thin, typed wrapper around one product's endpoints.
"""

from __future__ import annotations

from .aviationstack import AviationstackClient
from .base import APILayerClient, APILayerConfig
from .coinlayer import CoinlayerClient
from .currencylayer import CurrencylayerClient
from .errors import APILayerAPIError, APILayerError, ConfigError
from .fixer import FixerClient
from .giflayer import GiflayerClient
from .ipstack import IpstackClient
from .mailboxlayer import MailboxlayerClient
from .marketstack import MarketstackClient
from .mediastack import MediastackClient
from .numverify import NumverifyClient
from .pdflayer import PdflayerClient
from .positionstack import PositionstackClient
from .scrapestack import ScrapestackClient
from .screenshotlayer import ScreenshotlayerClient
from .serpstack import SerpstackClient
from .streetlayer import StreetlayerClient
from .userstack import UserstackClient
from .vatlayer import VatlayerClient
from .weatherstack import WeatherstackClient

__all__ = [
    "APILayerClient",
    "APILayerConfig",
    "APILayerError",
    "APILayerAPIError",
    "ConfigError",
    "AviationstackClient",
    "CoinlayerClient",
    "CurrencylayerClient",
    "FixerClient",
    "GiflayerClient",
    "IpstackClient",
    "MailboxlayerClient",
    "MarketstackClient",
    "MediastackClient",
    "NumverifyClient",
    "PdflayerClient",
    "PositionstackClient",
    "ScrapestackClient",
    "ScreenshotlayerClient",
    "SerpstackClient",
    "StreetlayerClient",
    "UserstackClient",
    "VatlayerClient",
    "WeatherstackClient",
]
