"""Pdflayer — convert HTML or a URL into a PDF.

https://pdflayer.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class PdflayerClient(APILayerClient):
    default_base_url = "http://api.pdflayer.com/api"
    service_env_name = "PDFLAYER"

    def convert_url(
        self, document_url: str, *, page_size: str = "A4", orientation: str = "portrait"
    ) -> bytes:
        """Render ``document_url`` to a PDF and return the raw bytes."""
        params: dict[str, Any] = {
            "document_url": document_url,
            "page_size": page_size,
            "orientation": orientation,
        }
        return self.request_raw("GET", "/convert", params=params).content

    def convert_html(
        self, document_html: str, *, page_size: str = "A4", orientation: str = "portrait"
    ) -> bytes:
        """Render raw ``document_html`` to a PDF and return the raw bytes."""
        params: dict[str, Any] = {
            "document_html": document_html,
            "page_size": page_size,
            "orientation": orientation,
        }
        return self.request_raw("GET", "/convert", params=params).content
