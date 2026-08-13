import math
import httpx
from backend.app.core.config import settings
TASK_TYPE_MAP = {
    "document": "RETRIEVAL_DOCUMENT",
    "query": "RETRIEVAL_QUERY",
}
class GeminiEmbeddingServiceError(
    RuntimeError
):
    pass
def normalize_embedding(
    values: list[float],
) -> list[float]:
    numbers = [
        float(value)
        for value in values
    ]
    if not numbers:
        raise GeminiEmbeddingServiceError(
            "Gemini returned an empty "
            "embedding vector."
        )
    if not all(
        math.isfinite(value)
        for value in numbers
    ):
        raise GeminiEmbeddingServiceError(
            "Gemini returned a non-finite "
            "embedding value."
        )
    magnitude = math.sqrt(
        sum(
            value * value
            for value in numbers
        )
    )
    if magnitude <= 0.0:
        raise GeminiEmbeddingServiceError(
            "Gemini returned a zero-length "
            "embedding vector."
        )
    return [
        value / magnitude
        for value in numbers
    ]
def embed_texts(
    texts: list[str],
    *,
    task_type: str,
) -> list[list[float]]:
    if not texts:
        return []
    gemini_task_type = TASK_TYPE_MAP.get(
        task_type
    )
    if gemini_task_type is None:
        raise GeminiEmbeddingServiceError(
            "Unsupported Gemini embedding "
            "task type."
        )
    api_key = (
        settings.gemini_api_key
        .strip()
    )
    if not api_key:
        raise GeminiEmbeddingServiceError(
            "GEMINI_API_KEY is not configured."
        )
    model = (
        settings.gemini_embedding_model
        .strip()
    )
    if not model:
        raise GeminiEmbeddingServiceError(
            "Gemini embedding model is "
            "not configured."
        )
    dimension = int(
        settings.gemini_embedding_dimension
    )
    model_resource = (
        model
        if model.startswith("models/")
        else f"models/{model}"
    )
    endpoint_model = (
        model_resource.removeprefix(
            "models/"
        )
    )
    endpoint = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        f"{endpoint_model}:batchEmbedContents"
    )
    requests = []
    for text_value in texts:
        normalized_text = str(
            text_value
        ).strip()
        if not normalized_text:
            raise GeminiEmbeddingServiceError(
                "Embedding input text cannot "
                "be empty."
            )
        requests.append(
            {
                "model": model_resource,
                "content": {
                    "parts": [
                        {
                            "text": normalized_text,
                        }
                    ],
                },
                "taskType": (
                    gemini_task_type
                ),
                "outputDimensionality": (
                    dimension
                ),
            }
        )
    try:
        with httpx.Client(
            timeout=180.0
        ) as client:
            response = client.post(
                endpoint,
                headers={
                    "x-goog-api-key": (
                        api_key
                    ),
                    "Content-Type": (
                        "application/json"
                    ),
                },
                json={
                    "requests": requests,
                },
            )
            response.raise_for_status()
    except httpx.HTTPError as error:
        raise GeminiEmbeddingServiceError(
            "Could not complete the Gemini "
            "embedding request."
        ) from error
    try:
        response_data = response.json()
    except ValueError as error:
        raise GeminiEmbeddingServiceError(
            "Gemini returned an invalid "
            "JSON response."
        ) from error
    raw_embeddings = (
        response_data.get(
            "embeddings"
        )
    )
    if not isinstance(
        raw_embeddings,
        list,
    ):
        raise GeminiEmbeddingServiceError(
            "Gemini returned an invalid "
            "embedding response."
        )
    if len(raw_embeddings) != len(
        texts
    ):
        raise GeminiEmbeddingServiceError(
            "The number of Gemini embeddings "
            "did not match the input texts."
        )
    embeddings: list[
        list[float]
    ] = []
    for raw_embedding in raw_embeddings:
        if not isinstance(
            raw_embedding,
            dict,
        ):
            raise GeminiEmbeddingServiceError(
                "Gemini returned an invalid "
                "embedding object."
            )
        raw_values = raw_embedding.get(
            "values"
        )
        if not isinstance(
            raw_values,
            list,
        ):
            raise GeminiEmbeddingServiceError(
                "Gemini returned an invalid "
                "embedding vector."
            )
        if len(raw_values) != dimension:
            raise GeminiEmbeddingServiceError(
                "Gemini embedding dimension "
                "did not match configuration."
            )
        embeddings.append(
            normalize_embedding(
                raw_values
            )
        )
    return embeddings
