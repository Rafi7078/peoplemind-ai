from typing import Any
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.document import Document
from backend.app.models.document_chunk import DocumentChunk
from backend.app.models.document_page import DocumentPage
from backend.app.services.chunking_service import (
    split_text_into_chunks,
)
from backend.app.services.ollama_embedding_service import (
    EmbeddingServiceError,
    embed_texts,
)
from backend.app.services.pdf_extraction_service import (
    DocumentNotFoundError,
    get_document,
)
from backend.app.services.vector_store_service import (
    get_vector_collection,
)
class DocumentIndexingError(RuntimeError):
    pass
class DocumentSearchError(RuntimeError):
    pass
def create_embedding_batches(
    texts: list[str],
) -> list[list[float]]:
    all_embeddings: list[list[float]] = []
    batch_size = settings.embedding_batch_size
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        all_embeddings.extend(embed_texts(batch))
    return all_embeddings
def index_document(
    database: Session,
    document_id: int,
) -> dict[str, int | str]:
    document = get_document(
        database=database,
        document_id=document_id,
    )
    if document.status not in {"ready", "indexed"}:
        raise DocumentIndexingError(
            "The document must be successfully processed "
            "before it can be indexed."
        )
    page_statement = (
        select(DocumentPage)
        .where(DocumentPage.document_id == document.id)
        .order_by(DocumentPage.page_number)
    )
    pages = list(
        database.scalars(page_statement).all()
    )
    if not pages:
        raise DocumentIndexingError(
            "No extracted document pages were found."
        )
    chunk_payloads: list[dict[str, Any]] = []
    for page in pages:
        page_chunks = split_text_into_chunks(
            text=page.text,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )
        for chunk_index, chunk_text in enumerate(
            page_chunks,
            start=1,
        ):
            vector_id = (
                f"document-{document.id}"
                f"-page-{page.page_number}"
                f"-chunk-{chunk_index}"
            )
            chunk_payloads.append(
                {
                    "document_id": document.id,
                    "document_name": document.original_name,
                    "page_number": page.page_number,
                    "chunk_index": chunk_index,
                    "vector_id": vector_id,
                    "text": chunk_text,
                    "char_count": len(chunk_text),
                }
            )
    if not chunk_payloads:
        raise DocumentIndexingError(
            "No searchable text chunks could be created."
        )
    chunk_texts = [
        payload["text"]
        for payload in chunk_payloads
    ]
    try:
        embeddings = create_embedding_batches(
            chunk_texts
        )
    except EmbeddingServiceError as error:
        raise DocumentIndexingError(
            str(error)
        ) from error
    if len(embeddings) != len(chunk_payloads):
        raise DocumentIndexingError(
            "Embedding generation returned an "
            "unexpected number of vectors."
        )
    collection = None
    new_vector_ids = [
        payload["vector_id"]
        for payload in chunk_payloads
    ]
    try:
        collection = get_vector_collection()
        existing_records = collection.get(
            where={"document_id": document.id},
        )
        existing_vector_ids = list(
            existing_records.get("ids") or []
        )
        if existing_vector_ids:
            collection.delete(
                ids=existing_vector_ids,
            )
        database.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_id == document.id
            )
        )
        chunk_models: list[DocumentChunk] = []
        for payload in chunk_payloads:
            chunk_models.append(
                DocumentChunk(
                    document_id=payload["document_id"],
                    page_number=payload["page_number"],
                    chunk_index=payload["chunk_index"],
                    vector_id=payload["vector_id"],
                    text=payload["text"],
                    char_count=payload["char_count"],
                )
            )
        database.add_all(chunk_models)
        collection.upsert(
            ids=new_vector_ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=[
                {
                    "document_id": payload["document_id"],
                    "document_name": payload["document_name"],
                    "page_number": payload["page_number"],
                    "chunk_index": payload["chunk_index"],
                }
                for payload in chunk_payloads
            ],
        )
        document.status = "indexed"
        database.commit()
    except Exception as error:
        database.rollback()
        if collection is not None and new_vector_ids:
            try:
                collection.delete(ids=new_vector_ids)
            except Exception:
                pass
        raise DocumentIndexingError(
            "The document could not be stored "
            "in the vector index."
        ) from error
    return {
        "document_id": document.id,
        "status": document.status,
        "chunk_count": len(chunk_payloads),
        "vector_dimension": len(embeddings[0]),
        "total_characters": sum(
            payload["char_count"]
            for payload in chunk_payloads
        ),
    }
def list_document_chunks(
    database: Session,
    document_id: int,
) -> list[DocumentChunk]:
    get_document(
        database=database,
        document_id=document_id,
    )
    statement = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(
            DocumentChunk.page_number,
            DocumentChunk.chunk_index,
        )
    )
    return list(database.scalars(statement).all())
def search_document_chunks(
    query: str,
    top_k: int,
    document_id: int | None = None,
) -> list[dict[str, Any]]:
    normalized_query = query.strip()
    if not normalized_query:
        raise DocumentSearchError(
            "The search query cannot be empty."
        )
    try:
        query_embedding = embed_texts(
            [normalized_query]
        )[0]
        collection = get_vector_collection()
        if collection.count() == 0:
            return []
        query_arguments: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": [
                "documents",
                "metadatas",
                "distances",
            ],
        }
        if document_id is not None:
            query_arguments["where"] = {
                "document_id": document_id,
            }
        results = collection.query(
            **query_arguments
        )
    except EmbeddingServiceError as error:
        raise DocumentSearchError(
            str(error)
        ) from error
    except Exception as error:
        raise DocumentSearchError(
            "The vector search could not be completed."
        ) from error
    result_ids = (
        results.get("ids", [[]])[0]
        if results.get("ids")
        else []
    )
    result_documents = (
        results.get("documents", [[]])[0]
        if results.get("documents")
        else []
    )
    result_metadatas = (
        results.get("metadatas", [[]])[0]
        if results.get("metadatas")
        else []
    )
    result_distances = (
        results.get("distances", [[]])[0]
        if results.get("distances")
        else []
    )
    search_results: list[dict[str, Any]] = []
    for index, vector_id in enumerate(result_ids):
        metadata = result_metadatas[index] or {}
        search_results.append(
            {
                "vector_id": vector_id,
                "document_id": int(
                    metadata.get("document_id", 0)
                ),
                "document_name": str(
                    metadata.get("document_name", "")
                ),
                "page_number": int(
                    metadata.get("page_number", 0)
                ),
                "chunk_index": int(
                    metadata.get("chunk_index", 0)
                ),
                "distance": float(
                    result_distances[index]
                ),
                "text": str(
                    result_documents[index] or ""
                ),
            }
        )
    return search_results
