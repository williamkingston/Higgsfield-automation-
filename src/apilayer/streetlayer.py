"""Streetlayer — address autocomplete and validation.

https://streetlayer.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class StreetlayerClient(APILayerClient):
    default_base_url = "http://api.streetlayer.com/api"
    service_env_name = "STREETLAYER"

    def autocomplete(
        self, query: str, *, country: str | None = None, limit: int = 10
    ) -> dict[str, Any]:
        """Address autocomplete suggestions for a partial ``query``."""
        params: dict[str, Any] = {"query": query, "limit": limit}
        if country:
            params["country"] = country
        return self.request("GET", "/autocomplete", params=params)

    def validate(self, address: str, *, country: str | None = None) -> dict[str, Any]:
        """Validate and standardize a full ``address``."""
        params: dict[str, Any] = {"address": address}
        if country:
            params["country"] = country
        return self.request("GET", "/validate", params=params)
