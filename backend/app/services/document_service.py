from hashlib import sha256
from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.document import Document
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
