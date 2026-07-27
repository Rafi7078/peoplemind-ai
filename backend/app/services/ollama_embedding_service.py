import httpx
from backend.app.core.config import settings
class EmbeddingServiceError(RuntimeError):
    pass
def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    endpoint = (
        f"{settings.ollama_base_url.rstrip('/')}"
        "/api/embed"
    )
    payload = {
        "model": settings.ollama_embedding_model,
        "input": texts,
        "truncate": True,
    }
    try:
        with httpx.Client(timeout=180.0) as client:
            response = client.post(
                endpoint,
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPError as error:
        raise EmbeddingServiceError(
            "Could not connect to the local Ollama "
            "embedding service."
        ) from error
    response_data = response.json()
    raw_embeddings = response_data.get("embeddings")
    if not isinstance(raw_embeddings, list):
        raise EmbeddingServiceError(
            "Ollama returned an invalid embedding response."
        )
    if len(raw_embeddings) != len(texts):
        raise EmbeddingServiceError(
            "The number of embeddings did not match "
            "the number of input texts."
        )
    embeddings: list[list[float]] = []
    for raw_vector in raw_embeddings:
        if not isinstance(raw_vector, list) or not raw_vector:
            raise EmbeddingServiceError(
                "Ollama returned an empty embedding vector."
            )
        embeddings.append(
            [float(value) for value in raw_vector]
        )
    dimensions = {
        len(vector)
        for vector in embeddings
    }
    if len(dimensions) != 1:
        raise EmbeddingServiceError(
            "Embedding vectors have inconsistent dimensions."
        )
    return embeddings
