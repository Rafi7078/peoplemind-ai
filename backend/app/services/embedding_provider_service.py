from backend.app.core.config import settings
from backend.app.services.gemini_embedding_service import (
    GeminiEmbeddingServiceError,
    embed_texts as gemini_embed_texts,
)
from backend.app.services.ollama_embedding_service import (
    EmbeddingServiceError,
    embed_texts as ollama_embed_texts,
)
VALID_EMBEDDING_PROVIDERS = {
    "ollama",
    "gemini",
}
class EmbeddingProviderConfigurationError(
    ValueError
):
    pass
def get_embedding_provider() -> str:
    provider = (
        settings.embedding_provider
        .strip()
        .lower()
    )
    if (
        provider
        not in VALID_EMBEDDING_PROVIDERS
    ):
        raise EmbeddingProviderConfigurationError(
            "EMBEDDING_PROVIDER must be "
            "'ollama' or 'gemini'."
        )
    return provider
def embed_texts(
    texts: list[str],
    *,
    task_type: str = "document",
) -> list[list[float]]:
    provider = (
        get_embedding_provider()
    )
    if provider == "ollama":
        return ollama_embed_texts(
            texts
        )
    try:
        return gemini_embed_texts(
            texts,
            task_type=task_type,
        )
    except GeminiEmbeddingServiceError as error:
        raise EmbeddingServiceError(
            str(error)
        ) from error
