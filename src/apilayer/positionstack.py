"""Positionstack — forward and reverse geocoding.

https://positionstack.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class PositionstackClient(APILayerClient):
    default_base_url = "http://api.positionstack.com/v1"
    service_env_name = "POSITIONSTACK"

    def geocode(self, query: str, *, limit: int = 10, country: str | None = None) -> dict[str, Any]:
        """Forward geocode a free-text address or place name."""
        params: dict[str, Any] = {"query": query, "limit": limit}
        if country:
            params["country"] = country
        return self.request("GET", "/forward", params=params)

    def reverse_geocode(
        self, latitude: float, longitude: float, *, limit: int = 1
    ) -> dict[str, Any]:
        """Reverse geocode a coordinate pair into an address."""
        params = {"query": f"{latitude},{longitude}", "limit": limit}
        return self.request("GET", "/reverse", params=params)
