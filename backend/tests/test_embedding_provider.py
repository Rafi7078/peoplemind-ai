import pytest
import backend.app.services.embedding_provider_service as service
from backend.app.core.config import settings
from backend.app.services.ollama_embedding_service import (
    EmbeddingServiceError,
)
def test_ollama_provider_dispatch(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "embedding_provider",
        "ollama",
    )
    monkeypatch.setattr(
        service,
        "ollama_embed_texts",
        lambda texts: [
            [1.0, 2.0]
            for _ in texts
        ],
    )
    result = service.embed_texts(
        ["one", "two"],
        task_type="document",
    )
    assert result == [
        [1.0, 2.0],
        [1.0, 2.0],
    ]
def test_gemini_provider_dispatch(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "embedding_provider",
        "gemini",
    )
    received = {}
    def fake_embed(
        texts,
        *,
        task_type,
    ):
        received["texts"] = texts
        received["task_type"] = (
            task_type
        )
        return [
            [0.5]
            for _ in texts
        ]
    monkeypatch.setattr(
        service,
        "gemini_embed_texts",
        fake_embed,
    )
    result = service.embed_texts(
        ["policy"],
        task_type="query",
    )
    assert result == [[0.5]]
    assert received == {
        "texts": ["policy"],
        "task_type": "query",
    }
def test_invalid_embedding_provider(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "embedding_provider",
        "invalid",
    )
    with pytest.raises(
        service.EmbeddingProviderConfigurationError
    ):
        service.get_embedding_provider()
def test_gemini_error_maps_to_common_error(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "embedding_provider",
        "gemini",
    )
    def fail(
        texts,
        *,
        task_type,
    ):
        raise (
            service.GeminiEmbeddingServiceError(
                "Gemini unavailable"
            )
        )
    monkeypatch.setattr(
        service,
        "gemini_embed_texts",
        fail,
    )
    with pytest.raises(
        EmbeddingServiceError
    ):
        service.embed_texts(
            ["policy"],
            task_type="query",
        )
