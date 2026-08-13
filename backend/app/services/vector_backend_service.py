from backend.app.core.config import settings
VALID_VECTOR_BACKENDS = {
    "chroma",
    "pgvector",
}
class VectorBackendConfigurationError(
    ValueError
):
    pass
def get_vector_backend() -> str:
    backend = (
        settings.vector_backend
        .strip()
        .lower()
    )
    if backend not in VALID_VECTOR_BACKENDS:
        raise VectorBackendConfigurationError(
            "VECTOR_BACKEND must be "
            "'chroma' or 'pgvector'."
        )
    return backend
def use_pgvector() -> bool:
    return (
        get_vector_backend()
        == "pgvector"
    )
def use_chroma() -> bool:
    return (
        get_vector_backend()
        == "chroma"
    )
