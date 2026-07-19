"""ipstack — IP address geolocation.

https://ipstack.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class IpstackClient(APILayerClient):
    default_base_url = "http://api.ipstack.com"
    service_env_name = "IPSTACK"

    def lookup(self, ip: str = "check", *, fields: list[str] | None = None) -> dict[str, Any]:
        """Geolocation for ``ip`` (or ``"check"`` for the caller's own IP)."""
        params: dict[str, Any] = {}
        if fields:
            params["fields"] = ",".join(fields)
        return self.request("GET", f"/{ip}", params=params)

    def bulk_lookup(self, ips: list[str]) -> Any:
        """Geolocation for multiple IPs in a single request (paid plans only).

        Returns a list of results rather than the single-lookup dict shape.
        """
        return self.request("GET", f"/{','.join(ips)}")
