"""Mailboxlayer — email address validation and verification.

https://mailboxlayer.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class MailboxlayerClient(APILayerClient):
    default_base_url = "http://apilayer.net/api"
    service_env_name = "MAILBOXLAYER"

    def validate(
        self, email: str, *, smtp: bool = True, format: bool = True, catch_all: bool = False
    ) -> dict[str, Any]:
        """Validate ``email``, including syntax, MX, and optional SMTP checks."""
        params = {
            "email": email,
            "smtp": int(smtp),
            "format": int(format),
            "catch_all": int(catch_all),
        }
        return self.request("GET", "/check", params=params)
