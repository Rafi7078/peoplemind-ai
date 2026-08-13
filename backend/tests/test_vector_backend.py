import pytest
from backend.app.core.config import settings
from backend.app.services.vector_backend_service import (
    VectorBackendConfigurationError,
    get_vector_backend,
    use_chroma,
    use_pgvector,
)
def test_chroma_backend(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "vector_backend",
        "chroma",
    )
    assert (
        get_vector_backend()
        == "chroma"
    )
    assert use_chroma() is True
    assert use_pgvector() is False
def test_pgvector_backend(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "vector_backend",
        "pgvector",
    )
    assert (
        get_vector_backend()
        == "pgvector"
    )
    assert use_pgvector() is True
    assert use_chroma() is False
def test_invalid_vector_backend(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "vector_backend",
        "invalid",
    )
    with pytest.raises(
        VectorBackendConfigurationError
    ):
        get_vector_backend()
