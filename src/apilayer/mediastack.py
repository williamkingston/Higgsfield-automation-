"""Mediastack — real-time and historical news articles.

https://mediastack.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class MediastackClient(APILayerClient):
    default_base_url = "http://api.mediastack.com/v1"
    service_env_name = "MEDIASTACK"

    def news(
        self,
        *,
        keywords: str | None = None,
        countries: list[str] | None = None,
        languages: list[str] | None = None,
        categories: list[str] | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Live/historical news articles filtered by the given criteria."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if keywords:
            params["keywords"] = keywords
        if countries:
            params["countries"] = ",".join(countries)
        if languages:
            params["languages"] = ",".join(languages)
        if categories:
            params["categories"] = ",".join(categories)
        return self.request("GET", "/news", params=params)
