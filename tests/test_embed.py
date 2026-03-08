import httpx
import pytest
import respx

from passage_pipeline.embed import generate_embeddings, BATCH_SIZE


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


class TestGenerateEmbeddings:
    @respx.mock
    def test_single_batch(self):
        texts = ["hello world", "goodbye world"]
        respx.post(url__eq=API_URL).mock(
            return_value=httpx.Response(
                200, json=_mock_embedding_response(1024, 2)
            )
        )
        result = generate_embeddings(texts, ACCOUNT_ID, API_TOKEN)
        assert len(result) == 2
        assert len(result[0]) == 1024

    @respx.mock
    def test_multiple_batches(self):
        texts = [f"text {i}" for i in range(BATCH_SIZE + 10)]
        route = respx.post(url__eq=API_URL).mock(
            side_effect=[
                httpx.Response(
                    200, json=_mock_embedding_response(1024, BATCH_SIZE)
                ),
                httpx.Response(
                    200, json=_mock_embedding_response(1024, 10)
                ),
            ]
        )
        result = generate_embeddings(texts, ACCOUNT_ID, API_TOKEN)
        assert len(result) == BATCH_SIZE + 10
        assert route.call_count == 2

    @respx.mock
    def test_request_payload(self):
        texts = ["test text"]
        route = respx.post(url__eq=API_URL).mock(
            return_value=httpx.Response(
                200, json=_mock_embedding_response(1024, 1)
            )
        )
        generate_embeddings(texts, ACCOUNT_ID, API_TOKEN)
        request = route.calls[0].request
        assert request.headers["authorization"] == f"Bearer {API_TOKEN}"

    @respx.mock
    def test_retry_on_error(self):
        texts = ["text"]
        route = respx.post(url__eq=API_URL).mock(
            side_effect=[
                httpx.Response(500),
                httpx.Response(
                    200, json=_mock_embedding_response(1024, 1)
                ),
            ]
        )
        result = generate_embeddings(texts, ACCOUNT_ID, API_TOKEN)
        assert len(result) == 1
        assert route.call_count == 2

    @respx.mock
    def test_max_retries_exceeded(self):
        texts = ["text"]
        respx.post(url__eq=API_URL).mock(
            return_value=httpx.Response(500)
        )
        with pytest.raises(httpx.HTTPStatusError):
            generate_embeddings(texts, ACCOUNT_ID, API_TOKEN)

    @respx.mock
    def test_empty_input(self):
        result = generate_embeddings([], ACCOUNT_ID, API_TOKEN)
        assert result == []

    @respx.mock
    def test_env_fallback(self, monkeypatch):
        monkeypatch.setenv("CF_ACCOUNT_ID", ACCOUNT_ID)
        monkeypatch.setenv("CF_API_TOKEN", API_TOKEN)
        texts = ["text"]
        respx.post(url__eq=API_URL).mock(
            return_value=httpx.Response(
                200, json=_mock_embedding_response(1024, 1)
            )
        )
        result = generate_embeddings(texts)
        assert len(result) == 1
