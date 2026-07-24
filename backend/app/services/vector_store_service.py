from functools import lru_cache
from pathlib import Path
import chromadb
from backend.app.core.config import settings
@lru_cache
def get_chroma_client():
    vector_directory = Path(settings.vector_store_dir)
    vector_directory.mkdir(
        parents=True,
        exist_ok=True,
    )
    return chromadb.PersistentClient(
        path=str(vector_directory),
    )
@lru_cache
def get_vector_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=settings.vector_collection_name,
        metadata={
            "description": (
                "PeopleMind AI HR document chunks"
            )
        },
    )
