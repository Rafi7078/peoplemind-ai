import math
import pytest
from backend.app.services.gemini_embedding_service import (
    GeminiEmbeddingServiceError,
    normalize_embedding,
)
def test_normalize_embedding():
    result = normalize_embedding(
        [3.0, 4.0]
    )
    magnitude = math.sqrt(
        sum(
            value * value
            for value in result
        )
    )
    assert magnitude == pytest.approx(
        1.0
    )
def test_normalize_rejects_zero_vector():
    with pytest.raises(
        GeminiEmbeddingServiceError
    ):
        normalize_embedding(
            [0.0, 0.0]
        )
def test_normalize_rejects_non_finite():
    with pytest.raises(
        GeminiEmbeddingServiceError
    ):
        normalize_embedding(
            [1.0, math.inf]
        )

def test_gemini_batch_payload_shape(
    monkeypatch,
):
    import backend.app.services.gemini_embedding_service as service
    from backend.app.core.config import settings
    monkeypatch.setattr(
        settings,
        "gemini_api_key",
        "test-api-key",
    )
    monkeypatch.setattr(
        settings,
        "gemini_embedding_model",
        "gemini-embedding-001",
    )
    monkeypatch.setattr(
        settings,
        "gemini_embedding_dimension",
        768,
    )
    captured = {}
    class FakeResponse:
        def raise_for_status(self):
            return None
        def json(self):
            return {
                "embeddings": [
                    {
                        "values": [
                            1.0
                            for _ in range(768)
                        ]
                    }
                ]
            }
    class FakeClient:
        def __init__(
            self,
            *args,
            **kwargs,
        ):
            pass
        def __enter__(self):
            return self
        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            return False
        def post(
            self,
            endpoint,
            *,
            headers,
            json,
        ):
            captured["endpoint"] = endpoint
            captured["headers"] = headers
            captured["json"] = json
            return FakeResponse()
    monkeypatch.setattr(
        service.httpx,
        "Client",
        FakeClient,
    )
    result = service.embed_texts(
        ["HR leave policy"],
        task_type="document",
    )
    request = (
        captured["json"]["requests"][0]
    )
    assert request["taskType"] == (
        "RETRIEVAL_DOCUMENT"
    )
    assert (
        request["outputDimensionality"]
        == 768
    )
    assert (
        "embedContentConfig"
        not in request
    )
    assert len(result) == 1
    assert len(result[0]) == 768
