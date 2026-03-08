import httpx
import pytest
import respx

from passage_pipeline.embed import (
    generate_embeddings,
    _make_batches,
    MAX_BATCH_SIZE,
    MAX_BATCH_CHARS,
)


def _mock_embedding_response(dim: int, count: int) -> dict:
    return {
        "result": {
            "data": [[0.1] * dim for _ in range(count)],
        },
        "success": True,
    }


ACCOUNT_ID = "test-account"
API_TOKEN = "test-token"
API_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/baai/bge-m3"


class TestMakeBatches:
    def test_empty(self):
        assert _make_batches([]) == []

    def test_single_batch(self):
        texts = ["hello", "world"]
        batches = _make_batches(texts)
        assert len(batches) == 1
        assert batches[0] == texts

    def test_splits_by_count(self):
        texts = [f"t{i}" for i in range(MAX_BATCH_SIZE + 10)]
        batches = _make_batches(texts)
        assert len(batches) == 2
        assert len(batches[0]) == MAX_BATCH_SIZE
        assert len(batches[1]) == 10

    def test_splits_by_chars(self):
        # Each text is large enough that 2 texts exceed MAX_BATCH_CHARS
        big_text = "a" * (MAX_BATCH_CHARS // 2 + 1)
        texts = [big_text, big_text, big_text]
        batches = _make_batches(texts)
        assert len(batches) == 3
        assert all(len(b) == 1 for b in batches)


class TestGenerateEmbeddings:
    @respx.mock
    @pytest.mark.asyncio
    async def test_single_batch(self):
        texts = ["hello world", "goodbye world"]
        respx.post(url__eq=API_URL).mock(
            return_value=httpx.Response(
                200, json=_mock_embedding_response(1024, 2)
            )
        )
        result = await generate_embeddings(texts, ACCOUNT_ID, API_TOKEN)
        assert len(result) == 2
        assert len(result[0]) == 1024

    @respx.mock
    @pytest.mark.asyncio
    async def test_multiple_batches(self):
        texts = [f"text {i}" for i in range(MAX_BATCH_SIZE + 10)]
        route = respx.post(url__eq=API_URL).mock(
            side_effect=[
                httpx.Response(
                    200, json=_mock_embedding_response(1024, MAX_BATCH_SIZE)
                ),
                httpx.Response(
                    200, json=_mock_embedding_response(1024, 10)
                ),
            ]
        )
        result = await generate_embeddings(texts, ACCOUNT_ID, API_TOKEN)
        assert len(result) == MAX_BATCH_SIZE + 10
        assert route.call_count == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_request_payload(self):
        texts = ["test text"]
        route = respx.post(url__eq=API_URL).mock(
            return_value=httpx.Response(
                200, json=_mock_embedding_response(1024, 1)
            )
        )
        await generate_embeddings(texts, ACCOUNT_ID, API_TOKEN)
        request = route.calls[0].request
        assert request.headers["authorization"] == f"Bearer {API_TOKEN}"

    @respx.mock
    @pytest.mark.asyncio
    async def test_retry_on_error(self):
        texts = ["text"]
        route = respx.post(url__eq=API_URL).mock(
            side_effect=[
                httpx.Response(500),
                httpx.Response(
                    200, json=_mock_embedding_response(1024, 1)
                ),
            ]
        )
        result = await generate_embeddings(texts, ACCOUNT_ID, API_TOKEN)
        assert len(result) == 1
        assert route.call_count == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        texts = ["text"]
        respx.post(url__eq=API_URL).mock(
            return_value=httpx.Response(500)
        )
        with pytest.raises(httpx.HTTPStatusError):
            await generate_embeddings(texts, ACCOUNT_ID, API_TOKEN)

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_input(self):
        result = await generate_embeddings([], ACCOUNT_ID, API_TOKEN)
        assert result == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_env_fallback(self, monkeypatch):
        monkeypatch.setenv("CF_ACCOUNT_ID", ACCOUNT_ID)
        monkeypatch.setenv("CF_API_TOKEN", API_TOKEN)
        texts = ["text"]
        respx.post(url__eq=API_URL).mock(
            return_value=httpx.Response(
                200, json=_mock_embedding_response(1024, 1)
            )
        )
        result = await generate_embeddings(texts)
        assert len(result) == 1
