"""Marketstack — real-time, intraday, and historical stock market data.

https://marketstack.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class MarketstackClient(APILayerClient):
    default_base_url = "http://api.marketstack.com/v1"
    service_env_name = "MARKETSTACK"

    def end_of_day(
        self,
        symbols: list[str],
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """End-of-day (daily close) data for ``symbols``."""
        params: dict[str, Any] = {"symbols": ",".join(symbols), "limit": limit}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        return self.request("GET", "/eod", params=params)

    def intraday(self, symbols: list[str], *, interval: str = "1min") -> dict[str, Any]:
        """Intraday price data for ``symbols`` at ``interval`` granularity."""
        params = {"symbols": ",".join(symbols), "interval": interval}
        return self.request("GET", "/intraday", params=params)

    def tickers(self, *, search: str | None = None, limit: int = 100) -> dict[str, Any]:
        """Ticker reference data, optionally filtered by ``search``."""
        params: dict[str, Any] = {"limit": limit}
        if search:
            params["search"] = search
        return self.request("GET", "/tickers", params=params)
