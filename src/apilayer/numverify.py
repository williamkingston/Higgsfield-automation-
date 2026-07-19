"""Numverify — global phone number validation and lookup.

https://numverify.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class NumverifyClient(APILayerClient):
    default_base_url = "http://apilayer.net/api"
    service_env_name = "NUMVERIFY"

    def validate(self, number: str, *, country_code: str | None = None) -> dict[str, Any]:
        """Validate ``number`` and return carrier/line-type/location details."""
        params: dict[str, Any] = {"number": number}
        if country_code:
            params["country_code"] = country_code
        return self.request("GET", "/validate", params=params)
