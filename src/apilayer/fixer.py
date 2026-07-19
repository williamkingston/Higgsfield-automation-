"""Fixer — foreign exchange rates and currency conversion.

https://fixer.io/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class FixerClient(APILayerClient):
    default_base_url = "http://data.fixer.io/api"
    service_env_name = "FIXER"

    def latest(
        self, *, base: str | None = None, symbols: list[str] | None = None
    ) -> dict[str, Any]:
        """Latest exchange rates, optionally quoted against ``base``."""
        params: dict[str, Any] = {}
        if base:
            params["base"] = base
        if symbols:
            params["symbols"] = ",".join(symbols)
        return self.request("GET", "/latest", params=params)

    def historical(
        self, date: str, *, base: str | None = None, symbols: list[str] | None = None
    ) -> dict[str, Any]:
        """Exchange rates for a specific ``date`` (``YYYY-MM-DD``)."""
        params: dict[str, Any] = {}
        if base:
            params["base"] = base
        if symbols:
            params["symbols"] = ",".join(symbols)
        return self.request("GET", f"/{date}", params=params)

    def convert(self, from_currency: str, to_currency: str, amount: float) -> dict[str, Any]:
        """Convert ``amount`` of ``from_currency`` into ``to_currency``."""
        params = {"from": from_currency, "to": to_currency, "amount": amount}
        return self.request("GET", "/convert", params=params)
