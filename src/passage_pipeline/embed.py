import os
import time

import httpx

CF_API_BASE = "https://api.cloudflare.com/client/v4/accounts"
EMBEDDING_MODEL = "@cf/baai/bge-m3"
BATCH_SIZE = 50
MAX_RETRIES = 3
RETRY_DELAY = 2.0


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

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]

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
