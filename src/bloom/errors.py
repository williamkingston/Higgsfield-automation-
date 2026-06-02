class BloomError(Exception):
    """Base class for all Bloom client errors."""


class BloomConfigError(BloomError):
    """Raised when the client is misconfigured (e.g. missing API key)."""


class BloomAPIError(BloomError):
    """Raised when the Bloom API returns a non-2xx response."""

    def __init__(self, status_code: int, message: str, request_id: str | None = None):
        self.status_code = status_code
        self.request_id = request_id
        detail = f"Bloom API error {status_code}: {message}"
        if request_id:
            detail += f" (request_id={request_id})"
        super().__init__(detail)
