"""Coinlayer — real-time and historical cryptocurrency exchange rates.

https://coinlayer.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class CoinlayerClient(APILayerClient):
    default_base_url = "http://api.coinlayer.com"
    service_env_name = "COINLAYER"

    def live(
        self, *, symbols: list[str] | None = None, target: str | None = None
    ) -> dict[str, Any]:
        """Live exchange rates for one or more cryptocurrency ``symbols``."""
        params: dict[str, Any] = {}
        if symbols:
            params["symbols"] = ",".join(symbols)
        if target:
            params["target"] = target
        return self.request("GET", "/live", params=params)

    def historical(
        self, date: str, *, symbols: list[str] | None = None, target: str | None = None
    ) -> dict[str, Any]:
        """Historical exchange rates for ``date`` (``YYYY-MM-DD``)."""
        params: dict[str, Any] = {}
        if symbols:
            params["symbols"] = ",".join(symbols)
        if target:
            params["target"] = target
        return self.request("GET", f"/{date}", params=params)

    def list_symbols(self) -> dict[str, Any]:
        """All supported cryptocurrency symbols."""
        return self.request("GET", "/list")
