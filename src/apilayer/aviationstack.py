"""Aviationstack — real-time flight tracking and status data.

https://aviationstack.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class AviationstackClient(APILayerClient):
    default_base_url = "http://api.aviationstack.com/v1"
    service_env_name = "AVIATIONSTACK"

    def flights(
        self,
        *,
        flight_iata: str | None = None,
        dep_iata: str | None = None,
        arr_iata: str | None = None,
        flight_status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Real-time flight data, optionally filtered by flight/airport/status."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if flight_iata:
            params["flight_iata"] = flight_iata
        if dep_iata:
            params["dep_iata"] = dep_iata
        if arr_iata:
            params["arr_iata"] = arr_iata
        if flight_status:
            params["flight_status"] = flight_status
        return self.request("GET", "/flights", params=params)

    def airports(self, *, search: str | None = None, limit: int = 100) -> dict[str, Any]:
        """Airport reference data, optionally filtered by ``search``."""
        params: dict[str, Any] = {"limit": limit}
        if search:
            params["search"] = search
        return self.request("GET", "/airports", params=params)
