import logging
import time

import requests

from .config import BloomConfig
from .errors import BloomAPIError

logger = logging.getLogger(__name__)

MAX_RETRIES = 5
BACKOFF_BASE_SECONDS = 1.0


class BloomClient:
    """Single entry point for all Bloom API calls.

    Handles bearer authentication, JSON decoding, request-ID logging, and
    exponential backoff on ``429`` responses. Raw HTTP requests should never be
    made elsewhere in the codebase — route everything through this client.
    """

    def __init__(self, config: BloomConfig | None = None, session=None, timeout: float = 30.0):
        self.config = config or BloomConfig.from_env()
        self.session = session or requests.Session()
        self.timeout = timeout

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)

    def request(self, method: str, path: str, **kwargs):
        url = f"{self.config.api_base}/{path.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Accept": "application/json",
            **kwargs.pop("headers", {}),
        }

        request_id = None
        for attempt in range(MAX_RETRIES):
            response = self.session.request(
                method, url, headers=headers, timeout=self.timeout, **kwargs
            )
            request_id = response.headers.get("x-request-id")

            if response.status_code == 429 and attempt < MAX_RETRIES - 1:
                delay = _retry_delay(response, attempt)
                logger.warning(
                    "Bloom API rate limited (request_id=%s), retrying in %.1fs",
                    request_id,
                    delay,
                )
                time.sleep(delay)
                continue

            logger.info(
                "Bloom API %s %s -> %s (request_id=%s)",
                method,
                path,
                response.status_code,
                request_id,
            )

            if response.status_code >= 400:
                raise BloomAPIError(response.status_code, _safe_message(response), request_id)

            return response.json() if response.content else None

        raise BloomAPIError(429, "Rate limit exceeded after retries", request_id)


def _retry_delay(response, attempt: int) -> float:
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return float(retry_after)
        except ValueError:
            pass
    return BACKOFF_BASE_SECONDS * (2 ** attempt)


def _safe_message(response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.reason or "request failed"
    if isinstance(data, dict):
        return data.get("error") or data.get("message") or response.reason or "request failed"
    return response.reason or "request failed"
