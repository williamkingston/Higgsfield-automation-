"""Exception types shared by every APILayer product client.

Every error carries enough context (status code, APILayer error code/type) to
be actionable without logging full response bodies that may contain PII.
"""

from __future__ import annotations


class APILayerError(Exception):
    """Base class for all errors raised by the ``apilayer`` package."""


class ConfigError(APILayerError):
    """Raised when a product's required configuration is missing or invalid."""


class APILayerAPIError(APILayerError):
    """Raised when an APILayer product API returns an unsuccessful response.

    APILayer's products share a common failure envelope:
    ``{"success": false, "error": {"code": ..., "type": ..., "info": ...}}``.
    This exception carries that envelope's fields alongside the HTTP status.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: int | None = None,
        error_type: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.error_type = error_type
        super().__init__(message)
