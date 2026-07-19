"""Serpstack — real-time Google search engine results.

https://serpstack.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class SerpstackClient(APILayerClient):
    default_base_url = "http://api.serpstack.com"
    service_env_name = "SERPSTACK"

    def search(
        self,
        query: str,
        *,
        gl: str | None = None,
        hl: str | None = None,
        num: int = 10,
        page: int = 1,
    ) -> dict[str, Any]:
        """Google search results for ``query`` (``gl``/``hl`` set country/language)."""
        params: dict[str, Any] = {"query": query, "num": num, "page": page}
        if gl:
            params["gl"] = gl
        if hl:
            params["hl"] = hl
        return self.request("GET", "/search", params=params)
