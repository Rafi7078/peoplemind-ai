from pathlib import Path
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from backend.app.models.document import Document
from backend.app.models.document_page import DocumentPage
from backend.app.services.document_service import (
    DocumentFileNotFoundError,
    get_document_file,
)
class DocumentNotFoundError(ValueError):
    pass
class DocumentProcessingError(ValueError):
    pass
def get_document(
    database: Session,
    document_id: int,
) -> Document:
    document = database.get(Document, document_id)
    if document is None:
        raise DocumentNotFoundError(
            f"Document ID {document_id} was not found."
        )
    return document
def clean_extracted_text(text: str) -> str:
    cleaned_text = text.replace("\x00", "")
    lines = [
        line.rstrip()
        for line in cleaned_text.splitlines()
    ]
    return "\n".join(lines).strip()
def mark_document_failed(
    database: Session,
    document_id: int,
) -> None:
    database.rollback()
    document = database.get(Document, document_id)
    if document is not None:
        document.status = "failed"
        database.commit()
def process_pdf_document(
    database: Session,
    document_id: int,
) -> dict[str, int | str]:
    document = get_document(database, document_id)
    try:
        _, file_path = get_document_file(
            database=database,
            document_id=document_id,
        )
    except DocumentFileNotFoundError as error:
        document.status = "failed"
        database.commit()
        raise DocumentProcessingError(
            "The stored PDF file could not be found."
        ) from error
    document.status = "processing"
    database.commit()
    try:
        reader = PdfReader(str(file_path))
        if reader.is_encrypted:
            raise DocumentProcessingError(
                "Password-protected PDFs are not supported."
            )
        if len(reader.pages) == 0:
            raise DocumentProcessingError(
                "The PDF does not contain any pages."
            )
        extracted_pages: list[DocumentPage] = []
        total_characters = 0
        text_pages = 0
        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):
            extracted_text = page.extract_text() or ""
            cleaned_text = clean_extracted_text(
                extracted_text
            )
            character_count = len(cleaned_text)
            total_characters += character_count
            if character_count > 0:
                text_pages += 1
            extracted_pages.append(
                DocumentPage(
                    document_id=document.id,
                    page_number=page_number,
                    text=cleaned_text,
                    char_count=character_count,
                )
            )
        database.execute(
            delete(DocumentPage).where(
                DocumentPage.document_id == document.id
            )
        )
        database.add_all(extracted_pages)
        document.page_count = len(extracted_pages)
        document.status = (
            "ready"
            if total_characters > 0
            else "needs_ocr"
        )
        database.commit()
        database.refresh(document)
        return {
            "document_id": document.id,
            "status": document.status,
            "page_count": document.page_count,
            "text_pages": text_pages,
            "total_characters": total_characters,
        }
    except DocumentProcessingError:
        mark_document_failed(
            database=database,
            document_id=document_id,
        )
        raise
    except (
        PdfReadError,
        OSError,
        ValueError,
        TypeError,
    ) as error:
        mark_document_failed(
            database=database,
            document_id=document_id,
        )
        raise DocumentProcessingError(
            "The PDF could not be processed."
        ) from error
    except Exception as error:
        mark_document_failed(
            database=database,
            document_id=document_id,
        )
        raise DocumentProcessingError(
            "An unexpected PDF processing error occurred."
        ) from error
def list_document_pages(
    database: Session,
    document_id: int,
) -> list[DocumentPage]:
    get_document(database, document_id)
    statement = (
        select(DocumentPage)
        .where(DocumentPage.document_id == document_id)
        .order_by(DocumentPage.page_number)
    )
    return list(database.scalars(statement).all())
