"""Giflayer — convert video into GIF.

https://giflayer.com/documentation
"""

from __future__ import annotations

from typing import Any

from .base import APILayerClient


class GiflayerClient(APILayerClient):
    default_base_url = "http://api.giflayer.com"
    service_env_name = "GIFLAYER"

    def convert(
        self,
        video_url: str,
        *,
        start: float | None = None,
        duration: float | None = None,
        width: int | None = None,
    ) -> dict[str, Any]:
        """Convert the video at ``video_url`` into a GIF and return the job result."""
        params: dict[str, Any] = {"video_url": video_url}
        if start is not None:
            params["start"] = start
        if duration is not None:
            params["duration"] = duration
        if width is not None:
            params["width"] = width
        return self.request("GET", "/convert", params=params)
