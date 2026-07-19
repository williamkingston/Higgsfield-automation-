"""Userstack — user-agent lookup and device/browser/OS detection.

https://userstack.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class UserstackClient(APILayerClient):
    default_base_url = "http://api.userstack.com"
    service_env_name = "USERSTACK"

    def lookup(self, user_agent: str) -> dict[str, Any]:
        """Parse ``user_agent`` into device, browser, and OS details."""
        return self.request("GET", "/detect", params={"ua": user_agent})
