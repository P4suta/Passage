import json

import httpx
import pytest
import respx

from passage_pipeline.ingest import (
    delete_all_from_vectorize,
    upload_to_vectorize,
    VECTORIZE_BATCH_SIZE,
)
from passage_pipeline.models import TextChunk

ACCOUNT_ID = "test-account"
API_TOKEN = "test-token"
INDEX_NAME = "passage-index"
API_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}"
    f"/vectorize/v2/indexes/{INDEX_NAME}/upsert"
)


def _make_chunk(index: int) -> TextChunk:
    return TextChunk(
        chunk_id=f"test-book:{index:05d}",
        text=f"Text for chunk {index}",
        book_id="test-book",
        title="Test Book",
        author="Test Author",
        year=1900,
        language="en",
        chapter="Chapter 1",
        chunk_index=index,
    )


LIST_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}"
    f"/vectorize/v2/indexes/{INDEX_NAME}/list"
)
DELETE_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}"
    f"/vectorize/v2/indexes/{INDEX_NAME}/delete_by_ids"
)


class TestDeleteAllFromVectorize:
    @respx.mock
    def test_delete_vectors(self):
        vectors = [{"id": f"id-{i}"} for i in range(3)]
        respx.get(url__startswith=LIST_URL).mock(
            return_value=httpx.Response(200, json={
                "result": {"vectors": vectors, "nextCursor": None},
            })
        )
        delete_route = respx.post(url__eq=DELETE_URL).mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        count = delete_all_from_vectorize(ACCOUNT_ID, API_TOKEN)

        assert count == 3
        assert delete_route.call_count == 1
        body = json.loads(delete_route.calls[0].request.content)
        assert body["ids"] == ["id-0", "id-1", "id-2"]

    @respx.mock
    def test_delete_empty_index(self):
        respx.get(url__startswith=LIST_URL).mock(
            return_value=httpx.Response(200, json={
                "result": {"vectors": [], "nextCursor": None},
            })
        )

        count = delete_all_from_vectorize(ACCOUNT_ID, API_TOKEN)
        assert count == 0

    @respx.mock
    def test_delete_with_pagination(self):
        respx.get(url__startswith=LIST_URL).mock(side_effect=[
            httpx.Response(200, json={
                "result": {
                    "vectors": [{"id": f"id-{i}"} for i in range(3)],
                    "nextCursor": "page2",
                },
            }),
            httpx.Response(200, json={
                "result": {
                    "vectors": [{"id": f"id-{i}"} for i in range(3, 5)],
                    "nextCursor": None,
                },
            }),
        ])
        respx.post(url__eq=DELETE_URL).mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        count = delete_all_from_vectorize(ACCOUNT_ID, API_TOKEN)
        assert count == 5


class TestUploadToVectorize:
    @respx.mock
    @pytest.mark.asyncio
    async def test_single_batch(self):
        chunks = [_make_chunk(i) for i in range(3)]
        embeddings = [[0.1] * 1024 for _ in range(3)]
        route = respx.post(url__eq=API_URL).mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        await upload_to_vectorize(chunks, embeddings, ACCOUNT_ID, API_TOKEN)
        assert route.call_count == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_ndjson_format(self):
        chunks = [_make_chunk(0)]
        embeddings = [[0.5, 0.6]]
        route = respx.post(url__eq=API_URL).mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        await upload_to_vectorize(chunks, embeddings, ACCOUNT_ID, API_TOKEN)

        request = route.calls[0].request
        # Extract the multipart body — find the NDJSON content
        body = request.content
        # Parse NDJSON from multipart body
        # The body contains multipart form data with the ndjson file
        body_str = body.decode("utf-8", errors="replace")
        # Find the JSON line in the body
        lines = [l for l in body_str.split("\n") if l.startswith('{"id"')]
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["id"] == "test-book:00000"
        assert record["values"] == [0.5, 0.6]
        assert record["metadata"]["bookId"] == "test-book"
        assert record["metadata"]["chunkIndex"] == 0

    @respx.mock
    @pytest.mark.asyncio
    async def test_metadata_truncation(self):
        chunk = TextChunk(
            chunk_id="book:00000",
            text="x" * 3000,
            book_id="book",
            title="T" * 300,
            author="A" * 200,
            year=1900,
            language="en",
            chapter="C" * 300,
            chunk_index=0,
        )
        route = respx.post(url__eq=API_URL).mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        await upload_to_vectorize([chunk], [[0.1]], ACCOUNT_ID, API_TOKEN)

        body_str = route.calls[0].request.content.decode("utf-8", errors="replace")
        lines = [l for l in body_str.split("\n") if l.startswith('{"id"')]
        record = json.loads(lines[0])
        assert len(record["metadata"]["text"]) == 2000
        assert len(record["metadata"]["title"]) == 200
        assert len(record["metadata"]["author"]) == 100
        assert len(record["metadata"]["chapter"]) == 200

    @respx.mock
    @pytest.mark.asyncio
    async def test_multiple_batches(self):
        count = VECTORIZE_BATCH_SIZE + 5
        chunks = [_make_chunk(i) for i in range(count)]
        embeddings = [[0.1] * 4 for _ in range(count)]
        route = respx.post(url__eq=API_URL).mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        await upload_to_vectorize(chunks, embeddings, ACCOUNT_ID, API_TOKEN)
        assert route.call_count == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_input(self):
        await upload_to_vectorize([], [], ACCOUNT_ID, API_TOKEN)
        # No requests should be made

    @respx.mock
    @pytest.mark.asyncio
    async def test_auth_header(self):
        chunks = [_make_chunk(0)]
        embeddings = [[0.1]]
        route = respx.post(url__eq=API_URL).mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        await upload_to_vectorize(chunks, embeddings, ACCOUNT_ID, API_TOKEN)
        request = route.calls[0].request
        assert request.headers["authorization"] == f"Bearer {API_TOKEN}"
