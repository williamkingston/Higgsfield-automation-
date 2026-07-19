"""Currencylayer — exchange rates for 168 world currencies.

https://currencylayer.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class CurrencylayerClient(APILayerClient):
    default_base_url = "http://api.currencylayer.com"
    service_env_name = "CURRENCYLAYER"

    def live(
        self, *, source: str | None = None, currencies: list[str] | None = None
    ) -> dict[str, Any]:
        """Real-time exchange rates."""
        params: dict[str, Any] = {}
        if source:
            params["source"] = source
        if currencies:
            params["currencies"] = ",".join(currencies)
        return self.request("GET", "/live", params=params)

    def historical(
        self, date: str, *, source: str | None = None, currencies: list[str] | None = None
    ) -> dict[str, Any]:
        """Historical exchange rates for ``date`` (``YYYY-MM-DD``)."""
        params: dict[str, Any] = {"date": date}
        if source:
            params["source"] = source
        if currencies:
            params["currencies"] = ",".join(currencies)
        return self.request("GET", "/historical", params=params)

    def convert(self, from_currency: str, to_currency: str, amount: float) -> dict[str, Any]:
        """Convert ``amount`` of ``from_currency`` into ``to_currency``."""
        params = {"from": from_currency, "to": to_currency, "amount": amount}
        return self.request("GET", "/convert", params=params)

    def list_currencies(self) -> dict[str, Any]:
        """All supported currency codes and names."""
        return self.request("GET", "/list")
