"""Weatherstack — real-time, historical, and forecast weather data.

https://weatherstack.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class WeatherstackClient(APILayerClient):
    default_base_url = "http://api.weatherstack.com"
    service_env_name = "WEATHERSTACK"

    def current(self, query: str, *, units: str | None = None) -> dict[str, Any]:
        """Current conditions for ``query`` (city name, coordinates, IP, or zip)."""
        params: dict[str, Any] = {"query": query}
        if units:
            params["units"] = units
        return self.request("GET", "/current", params=params)

    def historical(
        self, query: str, date: str, *, units: str | None = None
    ) -> dict[str, Any]:
        """Historical weather for ``query`` on ``date`` (``YYYY-MM-DD``)."""
        params: dict[str, Any] = {"query": query, "historical_date": date}
        if units:
            params["units"] = units
        return self.request("GET", "/historical", params=params)

    def forecast(
        self, query: str, *, forecast_days: int = 3, units: str | None = None
    ) -> dict[str, Any]:
        """Forecast for ``query`` over the next ``forecast_days`` days."""
        params: dict[str, Any] = {"query": query, "forecast_days": forecast_days}
        if units:
            params["units"] = units
        return self.request("GET", "/forecast", params=params)
