import io
import json
import os
import time

import httpx

from passage_pipeline.models import TextChunk

CF_API_BASE = "https://api.cloudflare.com/client/v4/accounts"
VECTORIZE_BATCH_SIZE = 1000
MAX_RETRIES = 3
RETRY_DELAY = 2.0


def upload_to_vectorize(
    chunks: list[TextChunk],
    embeddings: list[list[float]],
    account_id: str | None = None,
    api_token: str | None = None,
    index_name: str = "passage-index",
) -> None:
    """Upload vectors to Vectorize in NDJSON format."""
    account_id = account_id or os.environ["CF_ACCOUNT_ID"]
    api_token = api_token or os.environ["CF_API_TOKEN"]

    url = (
        f"{CF_API_BASE}/{account_id}"
        f"/vectorize/v2/indexes/{index_name}/upsert"
    )
    headers = {"Authorization": f"Bearer {api_token}"}

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

        ndjson.seek(0)

        for attempt in range(MAX_RETRIES):
            try:
                ndjson.seek(0)
                resp = httpx.post(
                    url,
                    headers=headers,
                    files={"vectors": ("batch.ndjson", ndjson)},
                    timeout=120,
                )
                resp.raise_for_status()
                break
            except (httpx.HTTPStatusError, httpx.TransportError):
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(RETRY_DELAY * (attempt + 1))

        print(
            f"  Uploaded {min(i + VECTORIZE_BATCH_SIZE, len(chunks))}"
            f"/{len(chunks)} vectors"
        )
