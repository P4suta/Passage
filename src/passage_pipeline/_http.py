import httpx

CF_API_BASE = "https://api.cloudflare.com/client/v4/accounts"
MAX_RETRIES = 5
RETRY_DELAY = 3.0


def is_retryable(exc: httpx.HTTPStatusError) -> bool:
    """Return True if the HTTP error is worth retrying (5xx or 429)."""
    return exc.response.status_code >= 500 or exc.response.status_code == 429
