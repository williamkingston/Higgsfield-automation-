"""Screenshotlayer — website screenshot capture.

https://screenshotlayer.com/documentation

Pairs naturally with the ``website-to-hyperframes`` agent skill's capture
step: this client fetches the raw screenshot image bytes that skill's
pipeline turns into a HyperFrames video.
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class ScreenshotlayerClient(APILayerClient):
    default_base_url = "http://api.screenshotlayer.com/api"
    service_env_name = "SCREENSHOTLAYER"

    def capture(
        self,
        url: str,
        *,
        width: int = 1920,
        fullpage: bool = True,
        format: str = "PNG",
        viewport: str | None = None,
    ) -> bytes:
        """Capture ``url`` and return the raw image bytes."""
        params: dict[str, Any] = {
            "url": url,
            "width": width,
            "fullpage": int(fullpage),
            "format": format,
        }
        if viewport:
            params["viewport"] = viewport
        return self.request_raw("GET", "/capture", params=params).content
