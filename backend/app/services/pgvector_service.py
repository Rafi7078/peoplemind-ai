import math
from typing import Any
from sqlalchemy import text
from sqlalchemy.orm import Session
PGVECTOR_DIMENSION = 768
class PgVectorServiceError(
    RuntimeError
):
    pass
def vector_to_literal(
    vector: list[float],
) -> str:
    if len(vector) != PGVECTOR_DIMENSION:
        raise ValueError(
            "Embedding vector must contain "
            f"{PGVECTOR_DIMENSION} dimensions."
        )
    normalized: list[str] = []
    for value in vector:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(
                "Embedding vector contains "
                "a non-finite value."
            )
        normalized.append(
            repr(number)
        )
    return (
        "["
        + ",".join(normalized)
        + "]"
    )
def upsert_document_embedding(
    database: Session,
    *,
    chunk_id: int,
    vector_id: str,
    document_id: int,
    page_number: int,
    chunk_index: int,
    embedding: list[float],
) -> None:
    vector_literal = vector_to_literal(
        embedding
    )
    try:
        database.execute(
            text(
                """
                INSERT INTO public.document_embeddings (
                    chunk_id,
                    vector_id,
                    document_id,
                    page_number,
                    chunk_index,
                    embedding
                )
                VALUES (
                    :chunk_id,
                    :vector_id,
                    :document_id,
                    :page_number,
                    :chunk_index,
                    CAST(
                        :embedding
                        AS extensions.vector
                    )
                )
                ON CONFLICT (chunk_id)
                DO UPDATE SET
                    vector_id = EXCLUDED.vector_id,
                    document_id = EXCLUDED.document_id,
                    page_number = EXCLUDED.page_number,
                    chunk_index = EXCLUDED.chunk_index,
                    embedding = EXCLUDED.embedding
                """
            ),
            {
                "chunk_id": chunk_id,
                "vector_id": vector_id,
                "document_id": document_id,
                "page_number": page_number,
                "chunk_index": chunk_index,
                "embedding": vector_literal,
            },
        )
    except Exception as error:
        raise PgVectorServiceError(
            "The document embedding could "
            "not be stored."
        ) from error
def delete_document_embeddings(
    database: Session,
    *,
    document_id: int,
) -> None:
    try:
        database.execute(
            text(
                """
                DELETE FROM public.document_embeddings
                WHERE document_id = :document_id
                """
            ),
            {
                "document_id": document_id,
            },
        )
    except Exception as error:
        raise PgVectorServiceError(
            "Document embeddings could not "
            "be deleted."
        ) from error
def search_document_embeddings(
    database: Session,
    *,
    query_embedding: list[float],
    top_k: int,
    document_id: int | None = None,
) -> list[dict[str, Any]]:
    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than zero."
        )
    vector_literal = vector_to_literal(
        query_embedding
    )
    document_filter = ""
    parameters: dict[str, Any] = {
        "query_embedding": vector_literal,
        "top_k": top_k,
    }
    if document_id is not None:
        document_filter = (
            "AND e.document_id = :document_id"
        )
        parameters[
            "document_id"
        ] = document_id
    statement = text(
        f"""
        SELECT
            e.vector_id,
            e.document_id,
            d.original_name AS document_name,
            e.page_number,
            e.chunk_index,
            (
                e.embedding
                <=>
                CAST(
                    :query_embedding
                    AS extensions.vector
                )
            ) AS distance,
            c.text
        FROM public.document_embeddings AS e
        JOIN public.document_chunks AS c
            ON c.id = e.chunk_id
        JOIN public.documents AS d
            ON d.id = e.document_id
        WHERE 1 = 1
            {document_filter}
        ORDER BY
            e.embedding
            <=>
            CAST(
                :query_embedding
                AS extensions.vector
            )
        LIMIT :top_k
        """
    )
    try:
        rows = database.execute(
            statement,
            parameters,
        ).mappings().all()
    except Exception as error:
        raise PgVectorServiceError(
            "The pgvector search could "
            "not be completed."
        ) from error
    return [
        {
            "vector_id": str(
                row["vector_id"]
            ),
            "document_id": int(
                row["document_id"]
            ),
            "document_name": str(
                row["document_name"]
            ),
            "page_number": int(
                row["page_number"]
            ),
            "chunk_index": int(
                row["chunk_index"]
            ),
            "distance": float(
                row["distance"]
            ),
            "text": str(
                row["text"]
            ),
        }
        for row in rows
    ]
