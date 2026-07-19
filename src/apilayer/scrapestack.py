"""Scrapestack — proxy-backed real-time web scraping.

https://scrapestack.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class ScrapestackClient(APILayerClient):
    default_base_url = "http://api.scrapestack.com"
    service_env_name = "SCRAPESTACK"

    def scrape(
        self,
        url: str,
        *,
        render_js: bool = False,
        premium_proxy: bool = False,
        keep_headers: bool = False,
    ) -> str:
        """Fetch ``url`` through Scrapestack's proxy pool and return the raw body.

        Returns text rather than JSON — the target page's raw HTML/content is
        the response body itself, not an APILayer envelope.
        """
        params: dict[str, Any] = {
            "url": url,
            "render_js": int(render_js),
            "premium_proxy": int(premium_proxy),
            "keep_headers": int(keep_headers),
        }
        return self.request_raw("GET", "/scrape", params=params).text
