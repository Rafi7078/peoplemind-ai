from hashlib import sha256
from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.document import Document
from backend.app.models.document_chunk import DocumentChunk
from backend.app.models.document_page import DocumentPage
from backend.app.services.vector_store_service import (
    get_vector_collection,
)
READ_CHUNK_SIZE = 1024 * 1024
ALLOWED_PDF_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "application/octet-stream",
}
class DocumentValidationError(ValueError):
    pass
class DuplicateDocumentError(ValueError):
    def __init__(self, document_id: int) -> None:
        self.document_id = document_id
        super().__init__(
            f"This PDF has already been uploaded "
            f"(document ID: {document_id})."
        )
def list_documents(database: Session) -> list[Document]:
    statement = select(Document).order_by(Document.created_at.desc())
    return list(database.scalars(statement).all())
async def store_pdf_document(
    upload: UploadFile,
    database: Session,
    uploaded_by_id: int,
) -> Document:
    original_name = Path(upload.filename or "").name
    if not original_name:
        raise DocumentValidationError(
            "The uploaded file must have a filename."
        )
    if Path(original_name).suffix.lower() != ".pdf":
        raise DocumentValidationError(
            "Only PDF files are allowed."
        )
    if (
        upload.content_type
        and upload.content_type not in ALLOWED_PDF_CONTENT_TYPES
    ):
        raise DocumentValidationError(
            "The uploaded file has an unsupported content type."
        )
    upload_directory = Path(settings.document_upload_dir)
    upload_directory.mkdir(parents=True, exist_ok=True)
    upload_id = uuid4().hex
    temporary_path = upload_directory / f"{upload_id}.part"
    stored_name = f"{upload_id}.pdf"
    final_path = upload_directory / stored_name
    maximum_size_bytes = (
        settings.max_document_size_mb * 1024 * 1024
    )
    content_hasher = sha256()
    total_size = 0
    first_chunk = True
    try:
        with temporary_path.open("wb") as output_file:
            while True:
                chunk = await upload.read(READ_CHUNK_SIZE)
                if not chunk:
                    break
                if first_chunk:
                    first_chunk = False
                    if not chunk.startswith(b"%PDF-"):
                        raise DocumentValidationError(
                            "The uploaded file does not contain "
                            "a valid PDF signature."
                        )
                total_size += len(chunk)
                if total_size > maximum_size_bytes:
                    raise DocumentValidationError(
                        "The PDF exceeds the maximum allowed "
                        f"size of {settings.max_document_size_mb} MB."
                    )
                content_hasher.update(chunk)
                output_file.write(chunk)
        if total_size == 0:
            raise DocumentValidationError(
                "The uploaded PDF is empty."
            )
        file_digest = content_hasher.hexdigest()
        existing_document = database.scalar(
            select(Document).where(
                Document.sha256 == file_digest
            )
        )
        if existing_document is not None:
            raise DuplicateDocumentError(
                existing_document.id
            )
        temporary_path.replace(final_path)
        document = Document(
            original_name=original_name,
            stored_name=stored_name,
            file_path=str(final_path),
            sha256=file_digest,
            size_bytes=total_size,
            mime_type=upload.content_type or "application/pdf",
            status="uploaded",
            page_count=None,
            uploaded_by_id=uploaded_by_id,
        )
        try:
            database.add(document)
            database.commit()
            database.refresh(document)
        except IntegrityError as error:
            database.rollback()
            if final_path.exists():
                final_path.unlink()
            existing_document = database.scalar(
                select(Document).where(
                    Document.sha256 == file_digest
                )
            )
            existing_id = (
                existing_document.id
                if existing_document is not None
                else 0
            )
            raise DuplicateDocumentError(
                existing_id
            ) from error
        except Exception:
            database.rollback()
            if final_path.exists():
                final_path.unlink()
            raise
        return document
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
        await upload.close()

class DocumentFileNotFoundError(FileNotFoundError):
    pass
def get_document_file(
    database: Session,
    document_id: int,
) -> tuple[Document, Path]:
    document = database.get(
        Document,
        document_id,
    )
    if document is None:
        raise DocumentFileNotFoundError(
            "The requested document was not found."
        )
    upload_directory = Path(
        settings.document_upload_dir
    ).resolve()
    document_path = Path(
        document.file_path
    ).resolve()
    try:
        document_path.relative_to(
            upload_directory
        )
    except ValueError as error:
        raise DocumentFileNotFoundError(
            "The requested document file is unavailable."
        ) from error
    if not document_path.is_file():
        raise DocumentFileNotFoundError(
            "The requested document file is unavailable."
        )
    return document, document_path

class ManagedDocumentNotFoundError(
    LookupError
):
    pass
class DocumentNameConflictError(
    ValueError
):
    pass
class DocumentManagementError(
    RuntimeError
):
    pass
def get_managed_document(
    database: Session,
    document_id: int,
) -> Document:
    document = database.get(
        Document,
        document_id,
    )
    if document is None:
        raise ManagedDocumentNotFoundError(
            "The requested document was not found."
        )
    return document
def resolve_managed_document_path(
    document: Document,
) -> Path:
    upload_directory = Path(
        settings.document_upload_dir
    ).resolve()
    document_path = Path(
        document.file_path
    ).resolve()
    try:
        document_path.relative_to(
            upload_directory
        )
    except ValueError as error:
        raise DocumentManagementError(
            "The stored document path is invalid."
        ) from error
    return document_path
def rename_document(
    database: Session,
    document_id: int,
    original_name: str,
) -> Document:
    document = get_managed_document(
        database=database,
        document_id=document_id,
    )
    normalized_name = original_name.strip()
    if document.original_name == normalized_name:
        return document
    conflicting_document_id = database.scalar(
        select(Document.id).where(
            func.lower(Document.original_name)
            == normalized_name.lower(),
            Document.id != document_id,
        )
    )
    if conflicting_document_id is not None:
        raise DocumentNameConflictError(
            "Another document already uses this name."
        )
    collection = None
    vector_ids: list[str] = []
    previous_metadatas: list[dict] = []
    try:
        if document.status == "indexed":
            collection = get_vector_collection()
            vector_records = collection.get(
                where={
                    "document_id": document.id,
                },
                include=["metadatas"],
            )
            vector_ids = list(
                vector_records.get("ids") or []
            )
            previous_metadatas = [
                dict(metadata or {})
                for metadata in (
                    vector_records.get(
                        "metadatas"
                    )
                    or []
                )
            ]
            if vector_ids:
                updated_metadatas = []
                for metadata in previous_metadatas:
                    updated_metadata = dict(
                        metadata
                    )
                    updated_metadata[
                        "document_id"
                    ] = document.id
                    updated_metadata[
                        "document_name"
                    ] = normalized_name
                    updated_metadatas.append(
                        updated_metadata
                    )
                collection.update(
                    ids=vector_ids,
                    metadatas=updated_metadatas,
                )
        document.original_name = normalized_name
        database.commit()
        database.refresh(document)
        return document
    except (
        ManagedDocumentNotFoundError,
        DocumentNameConflictError,
    ):
        raise
    except Exception as error:
        database.rollback()
        if (
            collection is not None
            and vector_ids
            and previous_metadatas
        ):
            try:
                collection.update(
                    ids=vector_ids,
                    metadatas=previous_metadatas,
                )
            except Exception:
                pass
        raise DocumentManagementError(
            "The document could not be renamed."
        ) from error
def _normalize_embeddings(
    raw_embeddings,
) -> list:
    if raw_embeddings is None:
        return []
    if hasattr(
        raw_embeddings,
        "tolist",
    ):
        return raw_embeddings.tolist()
    return list(raw_embeddings)
def delete_document(
    database: Session,
    document_id: int,
) -> dict[str, int | bool]:
    document = get_managed_document(
        database=database,
        document_id=document_id,
    )
    document_path = (
        resolve_managed_document_path(
            document
        )
    )
    collection = None
    vector_ids: list[str] = []
    vector_documents: list[str] = []
    vector_metadatas: list[dict] = []
    vector_embeddings: list = []
    if document.status == "indexed":
        try:
            collection = get_vector_collection()
            vector_records = collection.get(
                where={
                    "document_id": document.id,
                },
                include=[
                    "documents",
                    "metadatas",
                    "embeddings",
                ],
            )
            vector_ids = list(
                vector_records.get("ids") or []
            )
            vector_documents = list(
                vector_records.get(
                    "documents"
                )
                or []
            )
            vector_metadatas = [
                dict(metadata or {})
                for metadata in (
                    vector_records.get(
                        "metadatas"
                    )
                    or []
                )
            ]
            vector_embeddings = (
                _normalize_embeddings(
                    vector_records.get(
                        "embeddings"
                    )
                )
            )
        except Exception as error:
            raise DocumentManagementError(
                "The document vectors could not be prepared for deletion."
            ) from error
    staged_path: Path | None = None
    try:
        if document_path.exists():
            if not document_path.is_file():
                raise DocumentManagementError(
                    "The stored document path is not a file."
                )
            staged_path = (
                document_path.with_name(
                    "."
                    f"{document_path.name}."
                    f"{uuid4().hex}.deleting"
                )
            )
            document_path.replace(
                staged_path
            )
        if (
            collection is not None
            and vector_ids
        ):
            collection.delete(
                ids=vector_ids,
            )
        database.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_id
                == document.id
            )
        )
        database.execute(
            delete(DocumentPage).where(
                DocumentPage.document_id
                == document.id
            )
        )
        database.execute(
            delete(Document).where(
                Document.id == document.id
            )
        )
        database.commit()
    except Exception as error:
        database.rollback()
        if (
            collection is not None
            and vector_ids
            and len(vector_embeddings)
            == len(vector_ids)
        ):
            try:
                collection.upsert(
                    ids=vector_ids,
                    embeddings=vector_embeddings,
                    documents=vector_documents,
                    metadatas=vector_metadatas,
                )
            except Exception:
                pass
        if (
            staged_path is not None
            and staged_path.exists()
            and not document_path.exists()
        ):
            try:
                staged_path.replace(
                    document_path
                )
            except Exception:
                pass
        if isinstance(
            error,
            DocumentManagementError,
        ):
            raise
        raise DocumentManagementError(
            "The document could not be deleted."
        ) from error
    file_deleted = True
    if (
        staged_path is not None
        and staged_path.exists()
    ):
        try:
            staged_path.unlink()
        except OSError:
            file_deleted = False
    return {
        "document_id": document_id,
        "deleted": True,
        "file_deleted": file_deleted,
    }

