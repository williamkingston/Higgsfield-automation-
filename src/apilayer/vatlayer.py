"""Vatlayer — EU VAT number validation and VAT rates.

https://vatlayer.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class VatlayerClient(APILayerClient):
    default_base_url = "http://apilayer.net/api"
    service_env_name = "VATLAYER"

    def validate(self, vat_number: str) -> dict[str, Any]:
        """Validate an EU VAT number and return company/address details."""
        return self.request("GET", "/validate", params={"vat_number": vat_number})

    def rates(self) -> dict[str, Any]:
        """Current VAT rates for every EU member state."""
        return self.request("GET", "/rate_list")
