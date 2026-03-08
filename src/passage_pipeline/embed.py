import os
import time

import httpx

CF_API_BASE = "https://api.cloudflare.com/client/v4/accounts"
EMBEDDING_MODEL = "@cf/baai/bge-m3"
MAX_BATCH_CHARS = 40_000  # ~10k tokens safety margin under 60k token limit
MAX_BATCH_SIZE = 50
MAX_RETRIES = 3
RETRY_DELAY = 2.0


def _make_batches(texts: list[str]) -> list[list[str]]:
    """Split texts into batches respecting both item count and total character limits."""
    batches: list[list[str]] = []
    current: list[str] = []
    current_chars = 0

    for text in texts:
        text_len = len(text)
        if current and (
            len(current) >= MAX_BATCH_SIZE
            or current_chars + text_len > MAX_BATCH_CHARS
        ):
            batches.append(current)
            current = []
            current_chars = 0
        current.append(text)
        current_chars += text_len

    if current:
        batches.append(current)

    return batches


def generate_embeddings(
    texts: list[str],
    account_id: str | None = None,
    api_token: str | None = None,
) -> list[list[float]]:
    """Generate embeddings via Cloudflare Workers AI API."""
    account_id = account_id or os.environ["CF_ACCOUNT_ID"]
    api_token = api_token or os.environ["CF_API_TOKEN"]

    url = f"{CF_API_BASE}/{account_id}/ai/run/{EMBEDDING_MODEL}"
    headers = {"Authorization": f"Bearer {api_token}"}

    all_embeddings: list[list[float]] = []
    batches = _make_batches(texts)

    for batch in batches:
        for attempt in range(MAX_RETRIES):
            try:
                resp = httpx.post(
                    url,
                    headers=headers,
                    json={"text": batch},
                    timeout=120,
                )
                resp.raise_for_status()
                result = resp.json()
                all_embeddings.extend(result["result"]["data"])
                break
            except (httpx.HTTPStatusError, httpx.TransportError):
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(RETRY_DELAY * (attempt + 1))

        print(f"  Embedded {len(all_embeddings)}/{len(texts)} chunks")

    return all_embeddings
