import asyncio
import io
import json
import os
import time

import httpx

from passage_pipeline._http import CF_API_BASE, MAX_RETRIES, RETRY_DELAY, is_retryable
from passage_pipeline.models import TextChunk

VECTORIZE_BATCH_SIZE = 1000
VECTORIZE_DELETE_BATCH_SIZE = 100  # Cloudflare API limit for delete_by_ids


def delete_all_from_vectorize(
    account_id: str | None = None,
    api_token: str | None = None,
    index_name: str = "passage-index",
) -> int:
    """Delete all vectors from a Vectorize index. Returns the number deleted."""
    account_id = account_id or os.environ["CF_ACCOUNT_ID"]
    api_token = api_token or os.environ["CF_API_TOKEN"]

    base = f"{CF_API_BASE}/{account_id}/vectorize/v2/indexes/{index_name}"
    headers = {"Authorization": f"Bearer {api_token}"}

    deleted = 0
    cursor = None

    while True:
        params: dict[str, str | int] = {"count": 1000}
        if cursor:
            params["cursor"] = cursor

        for attempt in range(MAX_RETRIES):
            try:
                resp = httpx.get(
                    f"{base}/list", headers=headers, params=params, timeout=120,
                )
                resp.raise_for_status()
                break
            except httpx.HTTPStatusError as e:
                if not is_retryable(e) or attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(RETRY_DELAY * (attempt + 1))
            except httpx.TransportError:
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(RETRY_DELAY * (attempt + 1))

        data = resp.json()
        vectors = data.get("result", {}).get("vectors", [])
        if not vectors:
            break

        ids = [v["id"] for v in vectors]
        for batch_start in range(0, len(ids), VECTORIZE_DELETE_BATCH_SIZE):
            batch_ids = ids[batch_start : batch_start + VECTORIZE_DELETE_BATCH_SIZE]
            for attempt in range(MAX_RETRIES):
                try:
                    del_resp = httpx.post(
                        f"{base}/delete_by_ids",
                        headers=headers,
                        json={"ids": batch_ids},
                        timeout=120,
                    )
                    del_resp.raise_for_status()
                    break
                except httpx.HTTPStatusError as e:
                    if not is_retryable(e) or attempt == MAX_RETRIES - 1:
                        raise
                    time.sleep(RETRY_DELAY * (attempt + 1))
                except httpx.TransportError:
                    if attempt == MAX_RETRIES - 1:
                        raise
                    time.sleep(RETRY_DELAY * (attempt + 1))
            deleted += len(batch_ids)

        cursor = data.get("result", {}).get("nextCursor")
        if not cursor:
            break

    return deleted


async def upload_to_vectorize(
    chunks: list[TextChunk],
    embeddings: list[list[float]],
    account_id: str | None = None,
    api_token: str | None = None,
    index_name: str = "passage-index",
    *,
    client: httpx.AsyncClient | None = None,
) -> None:
    """Upload vectors to Vectorize in NDJSON format."""
    account_id = account_id or os.environ["CF_ACCOUNT_ID"]
    api_token = api_token or os.environ["CF_API_TOKEN"]

    url = (
        f"{CF_API_BASE}/{account_id}"
        f"/vectorize/v2/indexes/{index_name}/upsert"
    )
    headers = {"Authorization": f"Bearer {api_token}"}

    own_client = client is None
    if own_client:
        client = httpx.AsyncClient()

    try:
        for i in range(0, len(chunks), VECTORIZE_BATCH_SIZE):
            batch_chunks = chunks[i : i + VECTORIZE_BATCH_SIZE]
            batch_vectors = embeddings[i : i + VECTORIZE_BATCH_SIZE]

            ndjson = io.BytesIO()
            for chunk, vector in zip(batch_chunks, batch_vectors):
                record = {
                    "id": chunk.chunk_id,
                    "values": vector,
                    "metadata": {
                        "text": chunk.text[:2000],
                        "bookId": chunk.book_id,
                        "title": chunk.title[:200],
                        "author": chunk.author[:100],
                        "year": chunk.year,
                        "language": chunk.language,
                        "chapter": chunk.chapter[:200],
                        "chunkIndex": chunk.chunk_index,
                    },
                }
                ndjson.write(json.dumps(record).encode() + b"\n")

            for attempt in range(MAX_RETRIES):
                try:
                    ndjson.seek(0)
                    resp = await client.post(
                        url,
                        headers=headers,
                        files={"vectors": ("batch.ndjson", ndjson)},
                        timeout=120,
                    )
                    resp.raise_for_status()
                    break
                except httpx.HTTPStatusError as e:
                    if not is_retryable(e) or attempt == MAX_RETRIES - 1:
                        print(f"  Vectorize error: {e.response.text}", file=__import__('sys').stderr)
                        raise
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                except httpx.TransportError:
                    if attempt == MAX_RETRIES - 1:
                        raise
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))

            print(
                f"  Uploaded {min(i + VECTORIZE_BATCH_SIZE, len(chunks))}"
                f"/{len(chunks)} vectors"
            )
    finally:
        if own_client:
            await client.aclose()
